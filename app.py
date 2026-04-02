import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from agent import DataCenterProcurementAgent

st.set_page_config(
    page_title="AI Data Center Procurement Agent",
    page_icon="🖥️",
    layout="wide"
)

st.title("🖥️ AI Data Center Procurement Risk Agent")
st.caption("Real-time hardware risk analysis powered by live news signals and LLM reasoning")

# File upload section
uploaded_file = st.file_uploader("Upload hardware inventory CSV", type=["csv"])
use_sample = st.checkbox("Use sample inventory data")

file_to_use = None

if uploaded_file is not None:
    file_to_use = uploaded_file
elif use_sample:
    file_to_use = "data.csv"

if file_to_use is not None:
    # Initialize agent — this triggers __init__() which loads and processes everything
    if "agent" not in st.session_state:
        st.session_state.agent = DataCenterProcurementAgent(file_to_use)
    
    agent = st.session_state.agent
    dashboard = agent.get_dashboard_data()
# News refresh section
    st.subheader("📰 Live News Signals")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔄 Refresh News", type="primary"):
            with st.spinner("Fetching latest news and extracting signals..."):
                signals = agent.refresh_news()
                st.session_state.agent = agent
                st.success("News signals updated!")

    with col2:
        signals = dashboard["news_signals"]
        risk_color = {
            "High": "🔴",
            "Medium": "🟡", 
            "Low": "🟢"
        }.get(signals.get("overall_risk", "Medium"), "🟡")
        
        st.info(
            f"{risk_color} **Overall Market Risk: {signals.get('overall_risk', 'Medium')}**\n\n"
            f"💡 {signals.get('key_insight', 'No insight available')}"
        )

    # Show growth rates from news signals
    signal_cols = st.columns(6)
    categories = ["gpu", "server", "networking", "storage", "cooling", "power"]
    
    for i, cat in enumerate(categories):
        rate = signals.get(f"{cat}_growth_rate", 0.0)
        signal_cols[i].metric(
            label=cat.upper(),
            value=f"{rate*100:.1f}%",
            delta="weekly growth"
        )
# Summary metrics
    st.subheader("📊 Portfolio Risk Summary")
    
    metrics = dashboard["summary_metrics"]
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    
    m1.metric(
        label="Total SKUs",
        value=metrics["total_skus"]
    )
    m2.metric(
        label="🔴 Critical",
        value=metrics["critical_count"]
    )
    m3.metric(
        label="🟠 High",
        value=metrics["high_count"]
    )
    m4.metric(
        label="🟡 Medium",
        value=metrics["medium_count"]
    )
    m5.metric(
        label="🟢 Low",
        value=metrics["low_count"]
    )
    m6.metric(
        label="💰 Shortage Exposure",
        value=f"${metrics['total_shortage_cost']:,.0f}"
    )
    # Risk distribution chart and capacity chart side by side
    st.subheader("📈 Risk & Capacity Analysis")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.caption("Risk Distribution by SKU")
        risk_df = dashboard["full_data"]
        risk_order = ["Critical", "High", "Medium", "Low"]
        risk_counts = (
            risk_df["risk_level"]
            .fillna("Unknown")
            .value_counts()
            .reindex(risk_order, fill_value=0)
        )
        fig1, ax1 = plt.subplots()
        colors = ["#d62728", "#ff7f0e", "#ffdd57", "#2ca02c"]
        risk_counts.plot(kind="bar", ax=ax1, color=colors)
        ax1.set_title("Hardware Risk Distribution")
        ax1.set_xlabel("Risk Level")
        ax1.set_ylabel("Number of SKUs")
        ax1.tick_params(axis='x', rotation=0)
        st.pyplot(fig1)

    with chart_col2:
        st.caption("12-Week Capacity Scenarios by Category")
        capacity_df = dashboard["capacity_view"]
        category_capacity = capacity_df.groupby("Category").agg(
            base_stock=("base_stock", "mean"),
            optimistic_stock=("optimistic_stock", "mean"),
            pessimistic_stock=("pessimistic_stock", "mean")
        ).reset_index()
        
        fig2, ax2 = plt.subplots()
        x = range(len(category_capacity))
        width = 0.25
        ax2.bar([i - width for i in x], category_capacity["optimistic_stock"], 
                width=width, label="Optimistic", color="#2ca02c", alpha=0.8)
        ax2.bar(x, category_capacity["base_stock"], 
                width=width, label="Base", color="#1f77b4", alpha=0.8)
        ax2.bar([i + width for i in x], category_capacity["pessimistic_stock"], 
                width=width, label="Pessimistic", color="#d62728", alpha=0.8)
        ax2.axhline(y=0, color="black", linestyle="--", linewidth=0.8)
        ax2.set_xticks(list(x))
        ax2.set_xticklabels(category_capacity["Category"], rotation=45)
        ax2.set_title("Projected Stock After 12 Weeks")
        ax2.set_ylabel("Projected Units Remaining")
        ax2.legend()
        st.pyplot(fig2)
        
        st.subheader("🚧 Cluster Readiness")
        readiness = dashboard["cluster_readiness_summary"]

        r1, r2, r3 = st.columns(3)
        r1.metric("Blocking Categories", readiness["blocking_categories"])
        r2.metric("Watchlist Categories", readiness["watchlist_categories"])
        r3.metric("Highest-Risk Category", readiness["highest_risk_category"])

        st.warning(readiness["headline"])
    # Executive summary section
    st.subheader("📋 Executive Summary")
    
    summary_lines = []
    
    critical_count = metrics["critical_count"]
    high_count = metrics["high_count"]
    shortage_cost = metrics["total_shortage_cost"]
    
    top_risks_df = dashboard["top_risks"]
    reorder_df = dashboard["reorder_recommendations"]
    capacity_df = dashboard["capacity_view"]
    
    top_risk_skus = ", ".join(top_risks_df["SKU"].astype(str).head(3).tolist()) or "None"
    top_reorder_skus = ", ".join(reorder_df["SKU"].astype(str).head(3).tolist()) or "None"
    projected_shortfall = (capacity_df["capacity_risk"] == "Capacity Shortfall").sum()
    
    summary_lines = [
        f"{critical_count} SKUs are in Critical risk — immediate procurement action required.",
        f"Total shortage cost exposure is ${shortage_cost:,.0f}.",
        f"Highest risk SKUs: {top_risk_skus}.",
        f"Top reorder priorities: {top_reorder_skus}.",
        f"{projected_shortfall} SKUs projected to hit capacity shortfall within 12 weeks.",
        f"Market insight: {signals.get('key_insight', 'No insight available')}"
    ]
    

    for line in summary_lines:
        st.write(f"- {line}")

    # Download buttons
    st.subheader("⬇️ Download Reports")
    
    dl1, dl2, dl3, dl4 = st.columns(4)
    
    with dl1:
        st.download_button(
            label="Download Full Risk Table",
            data=dashboard["full_data"].to_csv(index=False).encode("utf-8"),
            file_name="datacenter_risk_table.csv",
            mime="text/csv"
        )
    with dl2:
        st.download_button(
            label="Download Top Risks",
            data=dashboard["top_risks"].to_csv(index=False).encode("utf-8"),
            file_name="top_risks.csv",
            mime="text/csv"
        )
    with dl3:
        st.download_button(
            label="Download Reorder Plan",
            data=dashboard["reorder_recommendations"].to_csv(index=False).encode("utf-8"),
            file_name="reorder_plan.csv",
            mime="text/csv"
        )

    with dl4:
        st.download_button(
            label="Download Blocker View",
            data=dashboard["deployment_blockers"].to_csv(index=False).encode("utf-8"),
            file_name="deployment_blockers.csv",
            mime="text/csv"
        )    
    # Data tables
    st.subheader("🗂️ Full Inventory Risk Table")
    st.dataframe(dashboard["full_data"], use_container_width=True)
    
    st.subheader("🔴 Top Risks")
    st.dataframe(dashboard["top_risks"], use_container_width=True)
    
    st.subheader("📦 Reorder Recommendations")
    st.dataframe(dashboard["reorder_recommendations"], use_container_width=True)

    st.subheader("🚧 Deployment Blockers by Category")
    st.caption("Categories flagged here are the ones most likely to delay cluster go-live.")

    blocker_cols = [
    "Category",
    "is_blocker",
    "blocker_reason",
    "shortfall_skus",
    "critical_procurement_skus",
    "high_procurement_skus",
    "avg_weeks_of_cover",
    "projected_pessimistic_stock",
    "shortage_cost",
    ]

    st.dataframe(
    dashboard["deployment_blockers"][blocker_cols],
    use_container_width=True
    )
    # Capacity projection table
    st.subheader("🔮 12-Week Capacity Projection")
    st.caption("Based on live news signals and scenario forecasting")
    
    capacity_cols = [
        "SKU", "Product", "Category",
        "Current_Stock", "Weekly_Demand",
        "base_stock", "optimistic_stock", "pessimistic_stock",
        "weeks_of_cover", "capacity_risk"
    ]
    st.dataframe(
        dashboard["capacity_view"][capacity_cols],
        use_container_width=True
    )

    # Ask the agent section
    st.subheader("💬 Ask the Agent")
    st.caption("Try: Which GPUs are critical? / Give me an action plan / What is blocking cluster deployment?")
    
    user_question = st.text_input("Ask a procurement question:")
    
    if st.button("Run Agent", type="primary") and user_question:
        with st.spinner("Agent thinking..."):
            result = agent.route(user_question)
        
        st.write(f"**Tool used:** `{result['tool_used']}`")
        
        # Show action plan if returned
        if result["action_plan"] is not None:
            plan = result["action_plan"]
            
            st.write("### ⚡ Immediate Actions")
            if plan.get("immediate_actions"):
                immediate_df = pd.DataFrame(plan["immediate_actions"])
                st.dataframe(immediate_df, use_container_width=True)
            
            st.write("### 📅 Quarterly Actions")
            if plan.get("quarterly_actions"):
                quarterly_df = pd.DataFrame(plan["quarterly_actions"])
                st.dataframe(quarterly_df, use_container_width=True)
            
            st.write("### 👀 Executive Watchouts")
            for watchout in plan.get("executive_watchouts", []):
                st.warning(watchout)
        
        # Show text response
        if result["text"] is not None:
            st.write("### Agent Response")
            st.write(result["text"])
        
        # Show supporting data table
        if result["data"] is not None:
            st.write("### Supporting Data")
            st.dataframe(result["data"], use_container_width=True)

else:
    st.info("👆 Upload a CSV file or check 'Use sample inventory data' to begin.")
    
    st.write("### What this agent does:")
    st.write("- 📦 Tracks GPU, server, networking, storage, cooling and power hardware risk")
    st.write("- 🌐 Fetches live news signals to adjust demand forecasts in real time")
    st.write("- 📊 Runs 3-scenario capacity projections (base, optimistic, pessimistic)")
    st.write("- 🚨 Flags critical procurement risks before they become capacity outages")
    st.write("- 💬 Answers natural language questions about your hardware portfolio")
    st.write("- ⚡ Generates structured action plans for procurement and capacity teams")