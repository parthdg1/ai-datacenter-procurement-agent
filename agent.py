from tools import (
    load_hardware_data,
    calculate_procurement_metrics,
    classify_procurement_risk,
    get_critical_items,
    get_top_risks,
    get_reorder_recommendations,
    get_summary_metrics,
    prepare_context_table,
    project_capacity_with_news,
    fetch_datacenter_news,
    extract_news_signals
)
from llm_helper import (
    generate_exec_summary,
    generate_category_insights,
    answer_procurement_question,
    generate_action_plan,
    score_resume_signal
)


class DataCenterProcurementAgent:

    def __init__(self, file):
        # Load and process data
        self.raw_df = load_hardware_data(file)
        self.metrics_df = calculate_procurement_metrics(self.raw_df)
        self.risk_df = classify_procurement_risk(self.metrics_df)

        # Default news signals before user refreshes
        self.news_signals = {
            "gpu_growth_rate": 0.08,
            "server_growth_rate": 0.04,
            "networking_growth_rate": 0.03,
            "storage_growth_rate": 0.02,
            "cooling_growth_rate": 0.01,
            "power_growth_rate": 0.01,
            "overall_risk": "Medium",
            "key_insight": "Using baseline growth rates. Click 'Refresh News' for live signals."
        }

        # Capacity projection using default signals
        self.capacity_df = project_capacity_with_news(self.raw_df, self.news_signals)

    def refresh_news(self):
        """Fetches live news and updates signals and capacity projections"""
        articles = fetch_datacenter_news()
        self.news_signals = extract_news_signals(articles)
        self.capacity_df = project_capacity_with_news(self.raw_df, self.news_signals)
        return self.news_signals

    def route(self, user_question: str) -> dict:
        q = user_question.lower()

        # Action plan routing
        if any(word in q for word in ["action", "plan", "what should i do", "next steps"]):
            critical_df = get_critical_items(self.risk_df)
            reorder_df = get_reorder_recommendations(self.risk_df)
            action_plan = generate_action_plan(
                critical_df.to_csv(index=False),
                reorder_df.to_csv(index=False),
                self.news_signals
            )
            return {
                "tool_used": "generate_action_plan",
                "data": critical_df,
                "text": None,
                "action_plan": action_plan
            }

        # Critical items routing
        if any(word in q for word in ["critical", "urgent", "immediate", "emergency"]):
            critical_df = get_critical_items(self.risk_df)
            return {
                "tool_used": "get_critical_items",
                "data": critical_df,
                "text": f"Found {len(critical_df)} critical/high risk items.",
                "action_plan": None
            }

        # Category insights routing
        if any(word in q for word in ["gpu", "server", "network", "storage", "cooling", "power", "category", "compare"]):
            category_summary = self.risk_df.groupby("Category").agg(
                total_skus=("SKU", "count"),
                avg_days_of_stock=("days_of_stock", "mean"),
                total_shortage_cost=("shortage_cost", "sum"),
                critical_count=("risk_level", lambda x: (x == "Critical").sum()),
                high_count=("risk_level", lambda x: (x == "High").sum())
            ).reset_index()
            insights = generate_category_insights(
                category_summary.to_csv(index=False),
                self.news_signals
            )
            return {
                "tool_used": "generate_category_insights",
                "data": category_summary,
                "text": insights,
                "action_plan": None
            }

        # Executive summary routing
        if any(word in q for word in ["summary", "overview", "executive", "brief", "report"]):
            summary_metrics = get_summary_metrics(self.risk_df)
            top_risks_df = get_top_risks(self.risk_df)
            reorder_df = get_reorder_recommendations(self.risk_df)
            summary = generate_exec_summary(
                summary_metrics,
                top_risks_df.to_csv(index=False),
                reorder_df.to_csv(index=False),
                self.news_signals,
                self.capacity_df.to_csv(index=False)
            )
            return {
                "tool_used": "generate_exec_summary",
                "data": top_risks_df,
                "text": summary,
                "action_plan": None
            }

        # Reorder routing
        if any(word in q for word in ["reorder", "order", "buy", "purchase", "procure"]):
            reorder_df = get_reorder_recommendations(self.risk_df)
            return {
                "tool_used": "get_reorder_recommendations",
                "data": reorder_df,
                "text": f"Generated reorder recommendations for {len(reorder_df)} items.",
                "action_plan": None
            }

        # Risk/shortage routing
        if any(word in q for word in ["risk", "shortage", "stockout", "top"]):
            top_df = get_top_risks(self.risk_df)
            summary_metrics = get_summary_metrics(self.risk_df)
            context_table = prepare_context_table(top_df)
            answer = answer_procurement_question(
                user_question,
                summary_metrics,
                context_table,
                self.news_signals
            )
            return {
                "tool_used": "get_top_risks + answer_procurement_question",
                "data": top_df,
                "text": answer,
                "action_plan": None
            }

        # Default — general question
        summary_metrics = get_summary_metrics(self.risk_df)
        context_table = prepare_context_table(self.risk_df)
        answer = answer_procurement_question(
            user_question,
            summary_metrics,
            context_table,
            self.news_signals
        )
        return {
            "tool_used": "answer_procurement_question",
            "data": None,
            "text": answer,
            "action_plan": None
        }

    def get_dashboard_data(self) -> dict:
        return {
            "full_data": self.risk_df,
            "summary_metrics": get_summary_metrics(self.risk_df),
            "top_risks": get_top_risks(self.risk_df),
            "critical_items": get_critical_items(self.risk_df),
            "reorder_recommendations": get_reorder_recommendations(self.risk_df),
            "capacity_view": self.capacity_df,
            "news_signals": self.news_signals
        }