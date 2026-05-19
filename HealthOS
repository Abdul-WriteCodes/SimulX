# ============================================================
# HEALTHFLOW — Single File Streamlit Business Health App
# SME Business Intelligence & Performance Monitoring System
# Stack: Streamlit + SQLite + Pandas + Plotly
# Deploy: Streamlit Cloud / Render / Railway
# ============================================================

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="HealthFlow",
    page_icon="🧠",
    layout="wide"
)

# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect(
    "healthflow.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS business_metrics (
    metric_id TEXT PRIMARY KEY,
    revenue REAL,
    expenses REAL,
    profit REAL,
    customers INTEGER,
    inventory_value REAL,
    recorded_at TEXT
)
""")

conn.commit()

# ============================================================
# HELPERS
# ============================================================

def gen_id():
    return str(uuid.uuid4())[:8].upper()

def fmt_currency(x):
    return f"₦{x:,.2f}"

def load_metrics():

    df = pd.read_sql_query(
        "SELECT * FROM business_metrics ORDER BY recorded_at DESC",
        conn
    )

    if not df.empty:

        numeric_cols = [
            "revenue",
            "expenses",
            "profit",
            "customers",
            "inventory_value"
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

        df["recorded_at"] = pd.to_datetime(
            df["recorded_at"]
        )

    return df

def add_metrics(
    revenue,
    expenses,
    customers,
    inventory_value
):

    profit = revenue - expenses

    cursor.execute("""
    INSERT INTO business_metrics VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        gen_id(),
        revenue,
        expenses,
        profit,
        customers,
        inventory_value,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()

def calculate_health_score(
    revenue,
    profit,
    expenses
):

    score = 0

    # Revenue Score
    if revenue >= 1000000:
        score += 35
    elif revenue >= 500000:
        score += 25
    elif revenue >= 100000:
        score += 15
    else:
        score += 5

    # Profitability Score
    if profit > 0:
        margin = (profit / revenue) * 100 if revenue > 0 else 0

        if margin >= 40:
            score += 35
        elif margin >= 20:
            score += 25
        elif margin >= 10:
            score += 15
        else:
            score += 5

    # Expense Control
    if revenue > 0:

        expense_ratio = (expenses / revenue) * 100

        if expense_ratio <= 40:
            score += 30
        elif expense_ratio <= 60:
            score += 20
        elif expense_ratio <= 80:
            score += 10

    return min(score, 100)

def get_health_status(score):

    if score >= 80:
        return "Excellent", "🟢"

    elif score >= 60:
        return "Healthy", "🟡"

    elif score >= 40:
        return "Warning", "🟠"

    else:
        return "Critical", "🔴"

# ============================================================
# STYLES
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #0f172a;
    color: white;
}

.metric-card {
    background: #111827;
    padding: 1rem;
    border-radius: 14px;
    border: 1px solid #1f2937;
    margin-bottom: 1rem;
}

.metric-title {
    font-size: 0.8rem;
    color: #94a3b8;
    text-transform: uppercase;
}

.metric-value {
    font-size: 1.8rem;
    font-weight: bold;
    color: white;
}

.health-card {
    background: linear-gradient(
        135deg,
        #111827,
        #1e293b
    );

    padding: 2rem;
    border-radius: 18px;
    border: 1px solid #334155;
    text-align: center;
}

.health-score {
    font-size: 4rem;
    font-weight: bold;
    color: #10b981;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🧠 HealthFlow")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Record Metrics",
        "Business Health",
        "Performance Analytics",
        "Insights"
    ]
)

# ============================================================
# LOAD DATA
# ============================================================

metrics_df = load_metrics()

# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("🧠 Business Health Dashboard")
    st.caption("Real-time business performance intelligence")

    if not metrics_df.empty:

        latest = metrics_df.iloc[0]

        revenue = latest["revenue"]
        expenses = latest["expenses"]
        profit = latest["profit"]

        health_score = calculate_health_score(
            revenue,
            profit,
            expenses
        )

        status, emoji = get_health_status(
            health_score
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "Revenue",
                fmt_currency(revenue)
            )

        with c2:
            st.metric(
                "Expenses",
                fmt_currency(expenses)
            )

        with c3:
            st.metric(
                "Profit",
                fmt_currency(profit)
            )

        with c4:
            st.metric(
                "Customers",
                int(latest["customers"])
            )

        st.markdown("---")

        st.markdown(f"""
        <div class="health-card">

            <div style="font-size:1.2rem;">
                Business Health Score
            </div>

            <div class="health-score">
                {health_score}
            </div>

            <div style="
                font-size:1.3rem;
                margin-top:1rem;
            ">
                {emoji} {status}
            </div>

        </div>
        """, unsafe_allow_html=True)

        # Revenue Trend
        st.subheader("Revenue Trend")

        trend_df = metrics_df.sort_values(
            "recorded_at"
        )

        fig = px.line(
            trend_df,
            x="recorded_at",
            y="revenue",
            markers=True
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # Profit Trend
        st.subheader("Profit Trend")

        fig2 = px.bar(
            trend_df,
            x="recorded_at",
            y="profit"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    else:
        st.info("No business data available.")

# ============================================================
# RECORD METRICS
# ============================================================

elif page == "Record Metrics":

    st.title("➕ Record Business Metrics")

    with st.form("metrics_form"):

        c1, c2 = st.columns(2)

        with c1:

            revenue = st.number_input(
                "Revenue",
                min_value=0.0
            )

            expenses = st.number_input(
                "Expenses",
                min_value=0.0
            )

        with c2:

            customers = st.number_input(
                "Customers",
                min_value=0,
                step=1
            )

            inventory_value = st.number_input(
                "Inventory Value",
                min_value=0.0
            )

        submitted = st.form_submit_button(
            "Save Metrics",
            use_container_width=True
        )

    if submitted:

        add_metrics(
            revenue,
            expenses,
            customers,
            inventory_value
        )

        st.success(
            "Business metrics recorded successfully."
        )

        st.rerun()

# ============================================================
# BUSINESS HEALTH
# ============================================================

elif page == "Business Health":

    st.title("📊 Business Health Analysis")

    if metrics_df.empty:
        st.info("No metrics available.")

    else:

        latest = metrics_df.iloc[0]

        revenue = latest["revenue"]
        expenses = latest["expenses"]
        profit = latest["profit"]

        health_score = calculate_health_score(
            revenue,
            profit,
            expenses
        )

        status, emoji = get_health_status(
            health_score
        )

        st.subheader("Current Health Status")

        st.markdown(f"""
        ## {emoji} {status}
        """)

        st.progress(
            health_score / 100
        )

        st.metric(
            "Health Score",
            f"{health_score}/100"
        )

        st.markdown("---")

        st.subheader("Health Breakdown")

        # Profit Margin
        margin = (
            (profit / revenue) * 100
            if revenue > 0 else 0
        )

        st.write(
            f"### Profit Margin: {margin:.1f}%"
        )

        if margin >= 30:
            st.success(
                "Excellent profitability."
            )

        elif margin >= 15:
            st.warning(
                "Moderate profitability."
            )

        else:
            st.error(
                "Low profitability detected."
            )

        # Expense Ratio
        expense_ratio = (
            (expenses / revenue) * 100
            if revenue > 0 else 0
        )

        st.write(
            f"### Expense Ratio: {expense_ratio:.1f}%"
        )

        if expense_ratio <= 40:
            st.success(
                "Good expense management."
            )

        elif expense_ratio <= 70:
            st.warning(
                "Expenses are increasing."
            )

        else:
            st.error(
                "Expenses are too high."
            )

# ============================================================
# PERFORMANCE ANALYTICS
# ============================================================

elif page == "Performance Analytics":

    st.title("📈 Performance Analytics")

    if metrics_df.empty:
        st.info("No data available.")

    else:

        metrics_df = metrics_df.sort_values(
            "recorded_at"
        )

        c1, c2 = st.columns(2)

        with c1:

            st.subheader("Revenue vs Expenses")

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=metrics_df["recorded_at"],
                    y=metrics_df["revenue"],
                    mode='lines+markers',
                    name='Revenue'
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=metrics_df["recorded_at"],
                    y=metrics_df["expenses"],
                    mode='lines+markers',
                    name='Expenses'
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with c2:

            st.subheader("Customer Growth")

            fig2 = px.bar(
                metrics_df,
                x="recorded_at",
                y="customers"
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

        st.subheader("Inventory Value Trend")

        fig3 = px.area(
            metrics_df,
            x="recorded_at",
            y="inventory_value"
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

# ============================================================
# INSIGHTS
# ============================================================

elif page == "Insights":

    st.title("🧠 Business Insights")

    if metrics_df.empty:
        st.info("No business data available.")

    else:

        latest = metrics_df.iloc[0]

        revenue = latest["revenue"]
        expenses = latest["expenses"]
        profit = latest["profit"]

        margin = (
            (profit / revenue) * 100
            if revenue > 0 else 0
        )

        expense_ratio = (
            (expenses / revenue) * 100
            if revenue > 0 else 0
        )

        st.subheader("Automated Recommendations")

        # Profitability Insight
        if margin < 10:

            st.error("""
            Your profit margin is critically low.

            Recommendations:
            - Increase product pricing
            - Reduce operational costs
            - Focus on high-margin products
            """)

        elif margin < 20:

            st.warning("""
            Your profit margin needs improvement.

            Recommendations:
            - Optimize expenses
            - Improve sales volume
            - Review supplier pricing
            """)

        else:

            st.success("""
            Your business profitability is healthy.

            Recommendations:
            - Scale marketing
            - Expand inventory
            - Invest in growth
            """)

        # Expense Insight
        if expense_ratio > 70:

            st.error("""
            Expenses are consuming too much revenue.

            Recommendations:
            - Reduce unnecessary spending
            - Negotiate supplier costs
            - Improve operational efficiency
            """)

        # Revenue Insight
        if revenue < 100000:

            st.warning("""
            Revenue is currently low.

            Recommendations:
            - Increase customer acquisition
            - Improve product visibility
            - Introduce promotions
            """)

        else:

            st.success("""
            Revenue performance is strong.

            Recommendations:
            - Maintain growth momentum
            - Expand product lines
            - Improve customer retention
            """)

# ============================================================
# FOOTER
# ============================================================

st.sidebar.markdown("---")
st.sidebar.caption("HealthFlow v1.0")
st.sidebar.caption("Built with Streamlit")
