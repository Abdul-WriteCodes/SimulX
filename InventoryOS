# ============================================================
# STOCKFLOW — Single File Streamlit Inventory Management App
# Lightweight Inventory & Stock Control System for SMEs
# Stack: Streamlit + SQLite + Pandas + Plotly
# Deploy: Streamlit Cloud / Render / Railway
# ============================================================

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import uuid

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="StockFlow",
    page_icon="📦",
    layout="wide"
)

# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect("stockflow.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    product_id TEXT PRIMARY KEY,
    product_name TEXT,
    category TEXT,
    stock_quantity INTEGER,
    cost_price REAL,
    selling_price REAL,
    reorder_level INTEGER,
    supplier TEXT,
    last_restocked TEXT,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS restock_log (
    log_id TEXT PRIMARY KEY,
    product_name TEXT,
    quantity_added INTEGER,
    previous_stock INTEGER,
    new_stock INTEGER,
    restocked_at TEXT
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

def load_inventory():

    df = pd.read_sql_query(
        "SELECT * FROM inventory ORDER BY created_at DESC",
        conn
    )

    if not df.empty:

        numeric_cols = [
            "stock_quantity",
            "cost_price",
            "selling_price",
            "reorder_level"
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

    return df

def load_restock_logs():

    df = pd.read_sql_query(
        "SELECT * FROM restock_log ORDER BY restocked_at DESC",
        conn
    )

    return df

def add_product(
    product_name,
    category,
    stock_quantity,
    cost_price,
    selling_price,
    reorder_level,
    supplier
):

    cursor.execute("""
    INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        gen_id(),
        product_name,
        category,
        stock_quantity,
        cost_price,
        selling_price,
        reorder_level,
        supplier,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()

def restock_product(
    product_id,
    quantity_added
):

    product_df = pd.read_sql_query(
        f"SELECT * FROM inventory WHERE product_id='{product_id}'",
        conn
    )

    if product_df.empty:
        return

    current_stock = int(product_df.iloc[0]["stock_quantity"])
    product_name = product_df.iloc[0]["product_name"]

    new_stock = current_stock + quantity_added

    cursor.execute("""
    UPDATE inventory
    SET stock_quantity=?,
        last_restocked=?
    WHERE product_id=?
    """, (
        new_stock,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        product_id
    ))

    cursor.execute("""
    INSERT INTO restock_log VALUES (?, ?, ?, ?, ?, ?)
    """, (
        gen_id(),
        product_name,
        quantity_added,
        current_stock,
        new_stock,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()

def delete_product(product_id):

    cursor.execute("""
    DELETE FROM inventory
    WHERE product_id=?
    """, (product_id,))

    conn.commit()

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

.low-stock {
    color: #f59e0b;
    font-weight: bold;
}

.out-stock {
    color: #ef4444;
    font-weight: bold;
}

.good-stock {
    color: #10b981;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📦 StockFlow")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Add Product",
        "Inventory",
        "Restock",
        "Analytics",
        "Restock Logs"
    ]
)

# ============================================================
# LOAD DATA
# ============================================================

inventory_df = load_inventory()
restock_df = load_restock_logs()

# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("📦 Inventory Dashboard")
    st.caption("Real-time inventory & stock monitoring")

    if not inventory_df.empty:

        total_products = len(inventory_df)

        total_stock = inventory_df["stock_quantity"].sum()

        inventory_value = (
            inventory_df["stock_quantity"] *
            inventory_df["cost_price"]
        ).sum()

        potential_revenue = (
            inventory_df["stock_quantity"] *
            inventory_df["selling_price"]
        ).sum()

        low_stock_count = len(
            inventory_df[
                inventory_df["stock_quantity"]
                <= inventory_df["reorder_level"]
            ]
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            st.metric(
                "Products",
                total_products
            )

        with c2:
            st.metric(
                "Total Stock",
                int(total_stock)
            )

        with c3:
            st.metric(
                "Inventory Value",
                fmt_currency(inventory_value)
            )

        with c4:
            st.metric(
                "Potential Revenue",
                fmt_currency(potential_revenue)
            )

        with c5:
            st.metric(
                "Low Stock",
                low_stock_count
            )

        # Low Stock Alerts
        st.subheader("⚠️ Low Stock Alerts")

        low_stock_df = inventory_df[
            inventory_df["stock_quantity"]
            <= inventory_df["reorder_level"]
        ]

        if low_stock_df.empty:
            st.success("All products are well stocked.")

        else:
            st.dataframe(
                low_stock_df[
                    [
                        "product_name",
                        "stock_quantity",
                        "reorder_level",
                        "supplier"
                    ]
                ],
                use_container_width=True
            )

        # Category Distribution
        st.subheader("Inventory Distribution")

        category_df = (
            inventory_df.groupby("category")["stock_quantity"]
            .sum()
            .reset_index()
        )

        fig = px.pie(
            category_df,
            names="category",
            values="stock_quantity"
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No products added yet.")

# ============================================================
# ADD PRODUCT
# ============================================================

elif page == "Add Product":

    st.title("➕ Add New Product")

    with st.form("product_form"):

        c1, c2 = st.columns(2)

        with c1:

            product_name = st.text_input(
                "Product Name"
            )

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

            stock_quantity = st.number_input(
                "Initial Stock",
                min_value=0,
                step=1
            )

            reorder_level = st.number_input(
                "Reorder Level",
                min_value=1,
                step=1
            )

        with c2:

            cost_price = st.number_input(
                "Cost Price",
                min_value=0.0
            )

            selling_price = st.number_input(
                "Selling Price",
                min_value=0.0
            )

            supplier = st.text_input(
                "Supplier Name"
            )

        submitted = st.form_submit_button(
            "Save Product",
            use_container_width=True
        )

    if submitted:

        if not product_name:
            st.error("Product name is required.")

        else:

            add_product(
                product_name,
                category,
                stock_quantity,
                cost_price,
                selling_price,
                reorder_level,
                supplier
            )

            st.success("Product added successfully.")
            st.rerun()

# ============================================================
# INVENTORY
# ============================================================

elif page == "Inventory":

    st.title("📋 Inventory List")

    if inventory_df.empty:
        st.info("No products available.")

    else:

        search = st.text_input(
            "Search Product"
        )

        filtered_df = inventory_df.copy()

        if search:

            filtered_df = filtered_df[
                filtered_df["product_name"]
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

        # Stock Status
        def stock_status(row):

            if row["stock_quantity"] <= 0:
                return "OUT OF STOCK"

            elif row["stock_quantity"] <= row["reorder_level"]:
                return "LOW STOCK"

            else:
                return "IN STOCK"

        filtered_df["status"] = filtered_df.apply(
            stock_status,
            axis=1
        )

        st.dataframe(
            filtered_df[
                [
                    "product_name",
                    "category",
                    "stock_quantity",
                    "reorder_level",
                    "cost_price",
                    "selling_price",
                    "supplier",
                    "status"
                ]
            ],
            use_container_width=True
        )

        st.subheader("Delete Product")

        product_options = {
            row["product_name"]: row["product_id"]
            for _, row in filtered_df.iterrows()
        }

        selected_product = st.selectbox(
            "Select Product",
            list(product_options.keys())
        )

        if st.button(
            "Delete Product",
            use_container_width=True
        ):

            delete_product(
                product_options[selected_product]
            )

            st.success("Product deleted.")
            st.rerun()

# ============================================================
# RESTOCK
# ============================================================

elif page == "Restock":

    st.title("🔄 Restock Product")

    if inventory_df.empty:
        st.info("No products available.")

    else:

        product_options = {
            f"{row['product_name']} ({row['stock_quantity']} left)": row["product_id"]
            for _, row in inventory_df.iterrows()
        }

        selected_product = st.selectbox(
            "Select Product",
            list(product_options.keys())
        )

        quantity_added = st.number_input(
            "Quantity to Add",
            min_value=1,
            step=1
        )

        if st.button(
            "Restock Product",
            use_container_width=True
        ):

            restock_product(
                product_options[selected_product],
                quantity_added
            )

            st.success("Product restocked successfully.")
            st.rerun()

# ============================================================
# ANALYTICS
# ============================================================

elif page == "Analytics":

    st.title("📈 Inventory Analytics")

    if inventory_df.empty:
        st.info("No data available.")

    else:

        # Most Valuable Inventory
        inventory_df["inventory_value"] = (
            inventory_df["stock_quantity"] *
            inventory_df["cost_price"]
        )

        top_value = (
            inventory_df.sort_values(
                "inventory_value",
                ascending=False
            )
            .head(10)
        )

        st.subheader("Highest Inventory Value")

        fig = px.bar(
            top_value,
            x="product_name",
            y="inventory_value"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # Potential Profit
        inventory_df["potential_profit"] = (
            (
                inventory_df["selling_price"]
                - inventory_df["cost_price"]
            )
            * inventory_df["stock_quantity"]
        )

        st.subheader("Potential Profit")

        fig2 = px.bar(
            inventory_df.sort_values(
                "potential_profit",
                ascending=False
            ).head(10),
            x="product_name",
            y="potential_profit"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

# ============================================================
# RESTOCK LOGS
# ============================================================

elif page == "Restock Logs":

    st.title("🧾 Restock History")

    if restock_df.empty:
        st.info("No restock logs available.")

    else:

        st.dataframe(
            restock_df,
            use_container_width=True
        )

# ============================================================
# FOOTER
# ============================================================

st.sidebar.markdown("---")
st.sidebar.caption("StockFlow v1.0")
st.sidebar.caption("Built with Streamlit")
