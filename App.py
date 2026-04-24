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

# ---------------- TOP NAVIGATION ----------------
menu = st.radio(
    "",
    ["🏠 Overview", "👥 Customers", "⚠️ Risk (Real Data)", "📊 Trends", "🎯 Decision Engine"],
    horizontal=True
)

# =====================================================
# 🏠 OVERVIEW
# =====================================================
if menu == "🏠 Overview":

    st.subheader("📊 Business Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"₹{df['TotalPrice'].sum():,.0f}")
    col2.metric("Transactions", len(df))
    col3.metric("Avg Value", f"₹{df['TotalPrice'].mean():.2f}")

    st.subheader("📈 Category Revenue")

    cat = df.groupby("category")["TotalPrice"].sum().reset_index()

    fig = px.bar(cat, x="category", y="TotalPrice", color="TotalPrice")
    st.plotly_chart(fig, use_container_width=True)


# =====================================================
# 👥 CUSTOMERS
# =====================================================
elif menu == "👥 Customers":

    st.subheader("👥 Customer Analysis")

    gen = df.groupby("gender")["TotalPrice"].mean().reset_index()

    fig = px.bar(gen, x="gender", y="TotalPrice",
                 color="TotalPrice",
                 text=gen["TotalPrice"].round(1))

    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    st.info("Shows average spending by customer group.")


# =====================================================
# ⚠️ RISK (REAL DATA)
# =====================================================
elif menu == "⚠️ Risk (Real Data)":

    st.subheader("⚠️ Risk Analysis (Real Data)")

    low = (df["TotalPrice"] < benchmark).mean() * 100
    safe = 100 - low

    st.metric("Low Value %", f"{low:.1f}%")

    pie = pd.DataFrame({
        "Type": ["Safe", "Risk"],
        "Value": [safe, low]
    })

    fig = px.pie(pie, names="Type", values="Value",
                 color="Type",
                 color_discrete_map={"Safe": "green", "Risk": "red"},
                 hole=0.5)

    st.plotly_chart(fig, use_container_width=True)

    st.info(f"{low:.1f}% transactions are below ₹{benchmark:.0f}")


# =====================================================
# 📊 TRENDS
# =====================================================
elif menu == "📊 Trends":

    st.subheader("📊 Sales Trends")

    trend = df.groupby("category")["TotalPrice"].mean().reset_index()

    fig = px.line(trend, x="category", y="TotalPrice", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.info("Shows trend of average sales across categories.")


# =====================================================
# 🎯 DECISION ENGINE
# =====================================================
elif menu == "🎯 Decision Engine":

    st.subheader("🎯 Business Decision Engine (Simulation)")

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

    chart_type = st.selectbox("Chart Type", ["Bar", "Pie", "Line"])

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

    def compute_risk(df):
        if df.empty:
            return 0, 0, 0, 0

        avg = df["TotalPrice"].mean()
        low_share = (df["TotalPrice"] < benchmark).mean() * 100
        safe = 100 - low_share

        return low_share, safe, avg

    if st.button("🚀 Analyze"):

        filtered = apply_filters(df)

        if filtered.empty:
            st.error("No data for filters")
            st.stop()

        risk, safe, avg = compute_risk(filtered)

        st.metric("Risk %", f"{risk:.1f}%")
        st.metric("Avg Value", f"₹{avg:.2f}")

        # Chart switch
        cat = filtered.groupby("category")["TotalPrice"].mean().reset_index()

        if chart_type == "Bar":
            fig = px.bar(cat, x="category", y="TotalPrice", color="TotalPrice")
        elif chart_type == "Pie":
            fig = px.pie(cat, names="category", values="TotalPrice")
        else:
            fig = px.line(cat, x="category", y="TotalPrice", markers=True)

        st.plotly_chart(fig, use_container_width=True)

        st.success(f"{risk:.1f}% transactions are low-value → indicates risk level")
