# ============================================================
# SALESFLOW — Single File Streamlit Sales Management App
# Lightweight SME Sales Tracker
# Stack: Streamlit + SQLite + Pandas + Plotly
# Deploy: Streamlit Cloud / Render / Railway
# ============================================================

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import uuid

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="SalesFlow",
    page_icon="📈",
    layout="wide"
)

# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect("salesflow.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    sale_id TEXT PRIMARY KEY,
    product_name TEXT,
    category TEXT,
    quantity INTEGER,
    unit_price REAL,
    total_amount REAL,
    cost_price REAL,
    gross_profit REAL,
    payment_method TEXT,
    customer_name TEXT,
    sale_date TEXT
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

def load_sales():
    df = pd.read_sql_query(
        "SELECT * FROM sales ORDER BY sale_date DESC",
        conn
    )

    if not df.empty:
        df["sale_date"] = pd.to_datetime(df["sale_date"])
        numeric_cols = [
            "quantity",
            "unit_price",
            "total_amount",
            "cost_price",
            "gross_profit"
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df

def add_sale(
    product_name,
    category,
    quantity,
    unit_price,
    cost_price,
    payment_method,
    customer_name
):
    total_amount = quantity * unit_price
    gross_profit = total_amount - (quantity * cost_price)

    cursor.execute("""
    INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        gen_id(),
        product_name,
        category,
        quantity,
        unit_price,
        total_amount,
        cost_price,
        gross_profit,
        payment_method,
        customer_name,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()

# ============================================================
# STYLES
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #0f172a;
}

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

.small-text {
    color: #94a3b8;
    font-size: 0.8rem;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📈 SalesFlow")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Record Sale",
        "Sales History",
        "Analytics"
    ]
)

# ============================================================
# LOAD DATA
# ============================================================

sales_df = load_sales()

# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("📊 Sales Dashboard")
    st.caption("Real-time sales performance overview")

    today = datetime.now().date()

    if not sales_df.empty:

        today_df = sales_df[
            sales_df["sale_date"].dt.date == today
        ]

        week_df = sales_df[
            sales_df["sale_date"] >= pd.Timestamp.now() - pd.Timedelta(days=7)
        ]

        month_df = sales_df[
            sales_df["sale_date"] >= pd.Timestamp.now() - pd.Timedelta(days=30)
        ]

        total_revenue = sales_df["total_amount"].sum()
        total_profit = sales_df["gross_profit"].sum()

        today_revenue = today_df["total_amount"].sum()
        week_revenue = week_df["total_amount"].sum()

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Today's Revenue</div>
                <div class="metric-value">{fmt_currency(today_revenue)}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Weekly Revenue</div>
                <div class="metric-value">{fmt_currency(week_revenue)}</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Revenue</div>
                <div class="metric-value">{fmt_currency(total_revenue)}</div>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Profit</div>
                <div class="metric-value">{fmt_currency(total_profit)}</div>
            </div>
            """, unsafe_allow_html=True)

        # Revenue Trend
        st.subheader("Revenue Trend")

        trend_df = (
            sales_df.groupby(
                sales_df["sale_date"].dt.date
            )["total_amount"]
            .sum()
            .reset_index()
        )

        fig = px.line(
            trend_df,
            x="sale_date",
            y="total_amount",
            markers=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # Top Products
        st.subheader("Top Selling Products")

        top_products = (
            sales_df.groupby("product_name")["quantity"]
            .sum()
            .reset_index()
            .sort_values("quantity", ascending=False)
            .head(10)
        )

        fig2 = px.bar(
            top_products,
            x="product_name",
            y="quantity"
        )

        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("No sales recorded yet.")

# ============================================================
# RECORD SALE
# ============================================================

elif page == "Record Sale":

    st.title("🛒 Record New Sale")

    with st.form("sale_form"):

        c1, c2 = st.columns(2)

        with c1:
            product_name = st.text_input("Product Name")
            category = st.selectbox(
                "Category",
                [
                    "Food",
                    "Fashion",
                    "Electronics",
                    "Drinks",
                    "Cosmetics",
                    "Other"
                ]
            )

            quantity = st.number_input(
                "Quantity",
                min_value=1,
                step=1
            )

            customer_name = st.text_input("Customer Name")

        with c2:
            unit_price = st.number_input(
                "Selling Price",
                min_value=0.0
            )

            cost_price = st.number_input(
                "Cost Price",
                min_value=0.0
            )

            payment_method = st.selectbox(
                "Payment Method",
                [
                    "Cash",
                    "Transfer",
                    "POS"
                ]
            )

        submitted = st.form_submit_button(
            "Save Sale",
            use_container_width=True
        )

    if submitted:

        if not product_name:
            st.error("Product name is required.")

        else:
            add_sale(
                product_name,
                category,
                quantity,
                unit_price,
                cost_price,
                payment_method,
                customer_name
            )

            st.success("Sale recorded successfully.")
            st.rerun()

# ============================================================
# SALES HISTORY
# ============================================================

elif page == "Sales History":

    st.title("📜 Sales History")

    if sales_df.empty:
        st.info("No sales available.")

    else:

        search = st.text_input("Search Product")

        filtered_df = sales_df.copy()

        if search:
            filtered_df = filtered_df[
                filtered_df["product_name"]
                .str.contains(search, case=False, na=False)
            ]

        display_df = filtered_df[
            [
                "product_name",
                "category",
                "quantity",
                "unit_price",
                "total_amount",
                "gross_profit",
                "payment_method",
                "sale_date"
            ]
        ]

        st.dataframe(
            display_df,
            use_container_width=True
        )

# ============================================================
# ANALYTICS
# ============================================================

elif page == "Analytics":

    st.title("📈 Sales Analytics")

    if sales_df.empty:
        st.info("No data available.")

    else:

        c1, c2 = st.columns(2)

        with c1:

            st.subheader("Revenue by Category")

            category_df = (
                sales_df.groupby("category")["total_amount"]
                .sum()
                .reset_index()
            )

            fig = px.pie(
                category_df,
                names="category",
                values="total_amount"
            )

            st.plotly_chart(fig, use_container_width=True)

        with c2:

            st.subheader("Payment Methods")

            payment_df = (
                sales_df.groupby("payment_method")["total_amount"]
                .sum()
                .reset_index()
            )

            fig2 = px.bar(
                payment_df,
                x="payment_method",
                y="total_amount"
            )

            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Best Selling Products")

        best_products = (
            sales_df.groupby("product_name")
            .agg({
                "quantity": "sum",
                "total_amount": "sum",
                "gross_profit": "sum"
            })
            .reset_index()
            .sort_values("total_amount", ascending=False)
        )

        st.dataframe(best_products, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================

st.sidebar.markdown("---")
st.sidebar.caption("SalesFlow v1.0")
st.sidebar.caption("Built with Streamlit")
