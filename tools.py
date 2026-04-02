import pandas as pd
import numpy as np
import feedparser
import requests
from groq import Groq
import os

def load_hardware_data(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    numeric_cols = ["Current_Stock", "Weekly_Demand", "Lead_Time_Days", "Reorder_Point", "Unit_Cost"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=numeric_cols).copy()
    return df

def calculate_procurement_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["daily_demand"] = df["Weekly_Demand"] / 7
    df["days_of_stock"] = df["Current_Stock"] / df["daily_demand"]
    df["lead_time_demand"] = df["daily_demand"] * df["Lead_Time_Days"]
    df["stock_gap"] = df["lead_time_demand"] - df["Current_Stock"]
    df["reorder_needed"] = df["Current_Stock"] < df["Reorder_Point"]
    df["shortage_units"] = df["stock_gap"].clip(lower=0)
    df["shortage_cost"] = df["shortage_units"] * df["Unit_Cost"]
    return df

def classify_procurement_risk(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def get_risk(row):
        if row["Current_Stock"] <= 0:
            return "Critical"
        if row["days_of_stock"] < row["Lead_Time_Days"]:
            return "High"
        if row["Current_Stock"] < row["Reorder_Point"]:
            return "Medium"
        return "Low"

    def get_priority_score(row):
        score = 0
        if row["Current_Stock"] <= 0:
            score += 100
        if row["days_of_stock"] < row["Lead_Time_Days"]:
            score += 50
        if row["Current_Stock"] < row["Reorder_Point"]:
            score += 25
        score += max(row["shortage_cost"], 0)
        return score

    df["risk_level"] = df.apply(get_risk, axis=1)
    df["priority_score"] = df.apply(get_priority_score, axis=1)
    return df.sort_values("priority_score", ascending=False).reset_index(drop=True)

def get_critical_items(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["risk_level"].isin(["Critical", "High"])].copy()

def get_top_risks(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    return df[df["risk_level"].isin(["Critical", "High", "Medium"])].head(n).copy()

def get_reorder_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["recommended_order_qty"] = (
        (df["lead_time_demand"] + df["Reorder_Point"] - df["Current_Stock"])
        .clip(lower=0)
        .round(0)
    )
    df["estimated_order_cost"] = df["recommended_order_qty"] * df["Unit_Cost"]
    result = df[df["recommended_order_qty"] > 0].copy()
    return result[["SKU", "Product", "Category", "Current_Stock", "Weekly_Demand",
                   "Lead_Time_Days", "risk_level", "recommended_order_qty",
                   "estimated_order_cost"]].sort_values("estimated_order_cost", ascending=False)

def get_summary_metrics(df: pd.DataFrame) -> dict:
    return {
        "total_skus": int(len(df)),
        "critical_count": int((df["risk_level"] == "Critical").sum()),
        "high_count": int((df["risk_level"] == "High").sum()),
        "medium_count": int((df["risk_level"] == "Medium").sum()),
        "low_count": int((df["risk_level"] == "Low").sum()),
        "total_shortage_cost": round(float(df["shortage_cost"].sum()), 2),
    }

def prepare_context_table(df: pd.DataFrame, limit: int = 10) -> str:
    cols = ["SKU", "Product", "Category", "Current_Stock", "Weekly_Demand",
            "Lead_Time_Days", "Reorder_Point", "days_of_stock",
            "stock_gap", "risk_level", "shortage_cost"]
    return df[cols].head(limit).round(2).to_csv(index=False)

def fetch_datacenter_news() -> list:
    queries = [
        "NVIDIA GPU supply chain",
        "data center hardware shortage",
        "semiconductor supply chain 2026",
        "AWS Google Microsoft data center expansion",
        "GPU procurement lead time"
    ]
    articles = []
    for query in queries:
        url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            articles.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "published": entry.get("published", "")
            })
    return articles

def extract_news_signals(articles: list) -> dict:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    news_text = "\n\n".join([
        f"Title: {a['title']}\nSummary: {a['summary']}"
        for a in articles[:10]
    ])
    
    prompt = f"""
You are a supply chain analyst for data center hardware.

Based on these recent news articles, extract demand signals and return ONLY a JSON object.
No explanation, just the JSON.

News articles:
{news_text}

Return this exact JSON format:
{{
    "gpu_growth_rate": 0.08,
    "server_growth_rate": 0.04,
    "networking_growth_rate": 0.03,
    "storage_growth_rate": 0.02,
    "cooling_growth_rate": 0.01,
    "power_growth_rate": 0.01,
    "overall_risk": "High",
    "key_insight": "One sentence summary of the biggest supply chain risk from the news"
}}

Use values between 0.01 and 0.20 for growth rates based on the news signals.
If news suggests high GPU demand, increase gpu_growth_rate.
If news suggests supply shortages, increase all rates.
"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a supply chain analyst. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    
    import json
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def project_capacity_with_news(df: pd.DataFrame, signals: dict, weeks_ahead: int = 12) -> pd.DataFrame:
    df = df.copy()

    category_growth = {
        "GPU": signals.get("gpu_growth_rate", 0.08),
        "Server": signals.get("server_growth_rate", 0.04),
        "Networking": signals.get("networking_growth_rate", 0.03),
        "Storage": signals.get("storage_growth_rate", 0.02),
        "Cooling": signals.get("cooling_growth_rate", 0.01),
        "Power": signals.get("power_growth_rate", 0.01)
    }

    df["trend_growth_rate"] = df["Category"].map(category_growth).fillna(0.02)

    df["base_demand"] = df["Weekly_Demand"] * (1 + df["trend_growth_rate"]) * weeks_ahead
    df["optimistic_demand"] = df["Weekly_Demand"] * (1 + df["trend_growth_rate"] * 0.5) * weeks_ahead
    df["pessimistic_demand"] = df["Weekly_Demand"] * (1 + df["trend_growth_rate"] * 2.0) * weeks_ahead

    df["base_stock"] = df["Current_Stock"] - df["base_demand"]
    df["optimistic_stock"] = df["Current_Stock"] - df["optimistic_demand"]
    df["pessimistic_stock"] = df["Current_Stock"] - df["pessimistic_demand"]

    df["weeks_of_cover"] = np.where(
        df["Weekly_Demand"] > 0,
        df["Current_Stock"] / df["Weekly_Demand"],
        np.inf
    )

    df["capacity_risk"] = np.select(
        [
            df["base_stock"] < 0,
            df["pessimistic_stock"] < 0,
            df["weeks_of_cover"] < 4,
            df["weeks_of_cover"] < 8
        ],
        [
            "Capacity Shortfall",
            "At Risk (Pessimistic)",
            "High Risk",
            "Medium Risk"
        ],
        default="Adequate"
    )

    return df

def summarize_category_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates procurement and capacity risk by hardware category.
    Useful for infrastructure planning discussions.
    """

    category_df = (
        df.groupby("Category")
        .agg(
            total_skus=("SKU", "count"),
            total_stock=("Current_Stock", "sum"),
            total_weekly_demand=("Weekly_Demand", "sum"),
            avg_lead_time=("Lead_Time_Days", "mean"),
            total_shortage_cost=("shortage_cost", "sum"),
            critical_items=("risk_level", lambda x: (x == "Critical").sum()),
            high_risk_items=("risk_level", lambda x: (x == "High").sum()),
        )
        .reset_index()
    )

    category_df["weeks_of_cover"] = (
        category_df["total_stock"] / category_df["total_weekly_demand"]
    )

    category_df = category_df.sort_values(
        "total_shortage_cost", ascending=False
    )

    return category_df

def get_cluster_readiness_report(risk_df: pd.DataFrame, capacity_df: pd.DataFrame):
    """
    Roll SKU-level procurement risk and scenario-based capacity risk up to the
    category level so the dashboard can answer: what is blocking cluster go-live?
    """
    blocker_df = (
        capacity_df.groupby("Category")
        .agg(
            total_skus=("SKU", "count"),
            shortfall_skus=("capacity_risk", lambda x: (x == "Capacity Shortfall").sum()),
            pessimistic_shortfall_skus=("pessimistic_stock", lambda x: (x < 0).sum()),
            avg_weeks_of_cover=("weeks_of_cover", "mean"),
            projected_base_stock=("base_stock", "sum"),
            projected_pessimistic_stock=("pessimistic_stock", "sum"),
        )
        .reset_index()
    )

    procurement_df = (
        risk_df.groupby("Category")
        .agg(
            critical_procurement_skus=("risk_level", lambda x: (x == "Critical").sum()),
            high_procurement_skus=("risk_level", lambda x: (x == "High").sum()),
            shortage_cost=("shortage_cost", "sum"),
        )
        .reset_index()
    )

    blocker_df = blocker_df.merge(procurement_df, on="Category", how="left").fillna(0)

    def classify_blocker(row):
        reasons = []
        status = "No"

        if row["critical_procurement_skus"] > 0:
            status = "Yes"
            reasons.append("critical procurement exposure")

        if row["shortfall_skus"] > 0:
            status = "Yes"
            reasons.append("base-case capacity shortfall")

        if status != "Yes" and row["pessimistic_shortfall_skus"] > 0:
            status = "Watch"
            reasons.append("pessimistic scenario shortfall")

        if status == "No" and row["avg_weeks_of_cover"] < 4:
            status = "Watch"
            reasons.append("low weeks of cover")

        if not reasons:
            reasons.append("no near-term deployment blocker")

        return pd.Series([status, "; ".join(reasons)])

    blocker_df[["is_blocker", "blocker_reason"]] = blocker_df.apply(classify_blocker, axis=1)

    blocker_df = blocker_df.sort_values(
        by=["is_blocker", "shortage_cost", "projected_pessimistic_stock"],
        ascending=[True, False, True],
        key=lambda s: s.map({"Yes": 0, "Watch": 1, "No": 2}) if s.name == "is_blocker" else s,
    ).reset_index(drop=True)

    blockers_only = blocker_df[blocker_df["is_blocker"] == "Yes"]
    watchlist = blocker_df[blocker_df["is_blocker"] == "Watch"]
    highest_risk_category = blocker_df.iloc[0]["Category"] if not blocker_df.empty else "None"

    summary = {
        "blocking_categories": int(len(blockers_only)),
        "watchlist_categories": int(len(watchlist)),
        "highest_risk_category": highest_risk_category,
        "headline": (
            "Cluster deployment is currently exposed by " + ", ".join(blockers_only["Category"].tolist())
            if not blockers_only.empty
            else "No immediate category-level deployment blocker identified."
        ),
    }

    return summary, blocker_df