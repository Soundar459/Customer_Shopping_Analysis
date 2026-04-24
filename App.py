import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("🧠 Retail Business Intelligence Dashboard")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    df = pd.read_excel("customer_shopping_data1.xlsx")
    df.columns = df.columns.str.strip()
    df["TotalPrice"] = df["price"] * df["quantity"]
    return df

df = load_data()

benchmark = df["TotalPrice"].median()

# ---------------- SIDEBAR MENU ----------------
st.sidebar.title("📂 Navigation")
menu = st.sidebar.radio("Select Section", ["📊 Dashboard", "🎯 Decision Engine"])

# =====================================================
# 📊 DASHBOARD SECTION
# =====================================================
if menu == "📊 Dashboard":

    st.subheader("📊 Overall Business Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"₹{df['TotalPrice'].sum():,.0f}")
    col2.metric("Transactions", len(df))
    col3.metric("Avg Transaction", f"₹{df['TotalPrice'].mean():.2f}")

    # Chart selector
    chart_type = st.selectbox("Select Chart Type", ["Bar", "Pie", "Line"])

    st.subheader("📈 Category Revenue")

    cat = df.groupby("category")["TotalPrice"].sum().reset_index()

    if chart_type == "Bar":
        fig = px.bar(cat, x="category", y="TotalPrice", color="TotalPrice")
    elif chart_type == "Pie":
        fig = px.pie(cat, names="category", values="TotalPrice")
    else:
        fig = px.line(cat, x="category", y="TotalPrice", markers=True)

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 🎯 DECISION ENGINE
# =====================================================
if menu == "🎯 Decision Engine":

    st.subheader("🎯 Business Decision Engine")

    col1, col2 = st.columns(2)

    gender = col1.selectbox("Gender", ["All"] + list(df["gender"].unique()))
    category = col1.selectbox("Category", ["All"] + list(df["category"].unique()))
    payment = col2.selectbox("Payment Method", ["All"] + list(df["payment_method"].unique()))

    price = col1.slider("Price Range",
                        int(df.price.min()),
                        int(df.price.max()),
                        (int(df.price.min()), int(df.price.max())))

    quantity = col2.slider("Quantity Range",
                           int(df.quantity.min()),
                           int(df.quantity.max()),
                           (int(df.quantity.min()), int(df.quantity.max())))

    # Chart selector
    chart_type = st.selectbox("Select Chart Type", ["Bar", "Pie", "Line"])

    # FILTER FUNCTION
    def apply_filters(df):
        f = df.copy()

        if gender != "All":
            f = f[f["gender"] == gender]

        if category != "All":
            f = f[f["category"] == category]

        if payment != "All":
            f = f[f["payment_method"] == payment]

        f = f[(f["price"] >= price[0]) & (f["price"] <= price[1])]
        f = f[(f["quantity"] >= quantity[0]) & (f["quantity"] <= quantity[1])]

        return f

    # RISK
    def compute_risk(df):
        if df.empty:
            return 0, 0, 0, 0

        avg = df["TotalPrice"].mean()
        low_share = (df["TotalPrice"] < benchmark).mean() * 100
        safe = 100 - low_share
        risk_score = low_share

        return risk_score, low_share, safe, avg

    def risk_level(score):
        if score < 30:
            return "Low"
        elif score < 60:
            return "Medium"
        return "High"

    # ANALYZE
    if st.button("🚀 Analyze"):

        filtered = apply_filters(df)

        if filtered.empty:
            st.error("No data for selected filters")
            st.stop()

        risk_score, low_share, safe_share, avg = compute_risk(filtered)
        level = risk_level(risk_score)

        # KPI
        c1, c2, c3 = st.columns(3)
        c1.metric("Risk Score", f"{risk_score:.1f}")
        c2.metric("Risk Level", level)
        c3.metric("Avg Value", f"₹{avg:.2f}")

        # Gauge
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            title={'text': "Risk Score"},
            gauge={'axis': {'range': [0, 100]}}
        ))
        st.plotly_chart(fig_g, use_container_width=True)

        # Safe vs Risk
        pie_df = pd.DataFrame({
            "Type": ["Safe", "Risk"],
            "Value": [safe_share, low_share]
        })

        fig = px.pie(pie_df, names="Type", values="Value",
                     color="Type",
                     color_discrete_map={"Safe": "green", "Risk": "red"},
                     hole=0.5)

        st.plotly_chart(fig, use_container_width=True)

        # Category chart with option
        st.subheader("📊 Category Analysis")

        cat = filtered.groupby("category")["TotalPrice"].mean().reset_index()

        if chart_type == "Bar":
            fig = px.bar(cat, x="category", y="TotalPrice", color="TotalPrice")
        elif chart_type == "Pie":
            fig = px.pie(cat, names="category", values="TotalPrice")
        else:
            fig = px.line(cat, x="category", y="TotalPrice", markers=True)

        st.plotly_chart(fig, use_container_width=True)

        # Insight
        st.subheader("💡 Insights")

        st.write(f"""
        - Risk Score: {risk_score:.1f} ({level})
        - Low-value transactions: {low_share:.1f}%
        - Average transaction: ₹{avg:.2f}

        👉 Higher low-value % = higher risk  
        👉 Better performance = higher transaction value  
        """)
