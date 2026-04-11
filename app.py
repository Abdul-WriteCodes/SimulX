import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="SimuX - Monte Carlo Simulator", layout="centered")

st.title("🎲 SimuX: Monte Carlo Simulation Platform")
st.markdown("Model uncertainty, simulate outcomes, and make data-driven decisions.")

# Sidebar Inputs
st.sidebar.header("🔧 Input Assumptions")

# Price
price_min = st.sidebar.slider("Price Min ($)", 1.0, 100.0, 10.0)
price_max = st.sidebar.slider("Price Max ($)", 1.0, 100.0, 15.0)

# Customers
cust_min = st.sidebar.slider("Customers Min", 10, 10000, 100)
cust_max = st.sidebar.slider("Customers Max", 10, 10000, 300)

# Conversion Rate
conv_min = st.sidebar.slider("Conversion Rate Min", 0.0, 0.5, 0.02)
conv_max = st.sidebar.slider("Conversion Rate Max", 0.0, 0.5, 0.05)

# Simulation runs
runs = st.sidebar.slider("Simulation Runs", 1000, 100000, 10000)

# Threshold for risk insight
threshold = st.sidebar.number_input("Risk Threshold ($)", value=5000)

st.markdown("---")

# Run Simulation
if st.button("🚀 Run Simulation"):

    # Generate random samples
    price = np.random.uniform(price_min, price_max, runs)
    customers = np.random.uniform(cust_min, cust_max, runs)
    conversion = np.random.uniform(conv_min, conv_max, runs)

    # Model
    revenue = price * customers * conversion

    # Statistics
    mean_rev = np.mean(revenue)
    std_rev = np.std(revenue)
    p10 = np.percentile(revenue, 10)
    p50 = np.percentile(revenue, 50)
    p90 = np.percentile(revenue, 90)

    # Display Results
    st.subheader("📊 Simulation Results")

    col1, col2 = st.columns(2)
    col1.metric("Mean Revenue", f"${mean_rev:,.2f}")
    col2.metric("Std Deviation", f"${std_rev:,.2f}")

    col3, col4, col5 = st.columns(3)
    col3.metric("P10", f"${p10:,.2f}")
    col4.metric("Median (P50)", f"${p50:,.2f}")
    col5.metric("P90", f"${p90:,.2f}")

    # Plot Histogram
    st.subheader("📈 Revenue Distribution")

    fig, ax = plt.subplots()
    ax.hist(revenue, bins=50)
    ax.set_title("Monte Carlo Revenue Distribution")
    ax.set_xlabel("Revenue")
    ax.set_ylabel("Frequency")

    st.pyplot(fig)

    # Risk Analysis
    prob_below_threshold = np.mean(revenue < threshold)

    st.subheader("🧠 AI Insight (Basic)")

    st.write(
        f"There is a **{prob_below_threshold * 100:.2f}% probability** that revenue falls below "
        f"**${threshold:,.2f}** based on your assumptions."
    )

    if prob_below_threshold > 0.5:
        st.warning("⚠️ High risk detected: More than half of outcomes fall below your threshold.")
    elif prob_below_threshold > 0.2:
        st.info("ℹ️ Moderate risk: Consider adjusting your assumptions.")
    else:
        st.success("✅ Low risk: Your model shows strong expected performance.")

else:
    st.info("Configure your assumptions in the sidebar and click 'Run Simulation'.")
