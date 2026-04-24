import streamlit as st
import pandas as pd
import plotly.express as px

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

# ---------------- MENU ----------------
menu = st.radio(
    "",
    ["🏠 Overview", "👥 Customers", "📦 Products", "💳 Payment", "🎯 Decision Engine"],
    horizontal=True
)

# =====================================================
# 🏠 OVERVIEW
# =====================================================
if menu == "🏠 Overview":

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"₹{df['TotalPrice'].sum():,.0f}")
    col2.metric("Transactions", len(df))
    col3.metric("Avg Value", f"₹{df['TotalPrice'].mean():.2f}")

    chart_type = st.selectbox("Choose Chart", ["Bar", "Pie"])

    cat = df.groupby("category")["TotalPrice"].sum().reset_index()

    if chart_type == "Bar":
        fig = px.bar(cat, x="category", y="TotalPrice",
                     color="TotalPrice", color_continuous_scale="Blues")
    else:
        fig = px.pie(cat, names="category", values="TotalPrice")

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 👥 CUSTOMERS
# =====================================================
elif menu == "👥 Customers":

    chart_type = st.selectbox("Choose Chart", ["Bar", "Pie"])

    gen = df.groupby("gender")["TotalPrice"].mean().reset_index()

    if chart_type == "Bar":
        fig = px.bar(gen, x="gender", y="TotalPrice",
                     color="gender",
                     color_discrete_map={"Male": "blue", "Female": "pink"},
                     text=gen["TotalPrice"].round(1))
    else:
        fig = px.pie(gen, names="gender", values="TotalPrice")

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 📦 PRODUCTS
# =====================================================
elif menu == "📦 Products":

    chart_type = st.selectbox("Choose Chart", ["Bar", "Pie", "Line"])

    cat = df.groupby("category")["TotalPrice"].mean().reset_index()

    if chart_type == "Bar":
        fig = px.bar(cat, x="category", y="TotalPrice",
                     color="TotalPrice", color_continuous_scale="Viridis")
    elif chart_type == "Line":
        fig = px.line(cat, x="category", y="TotalPrice")
    else:
        fig = px.pie(cat, names="category", values="TotalPrice")

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 💳 PAYMENT
# =====================================================
elif menu == "💳 Payment":

    chart_type = st.selectbox("Choose Chart", ["Bar", "Pie"])

    pay = df.groupby("payment_method")["TotalPrice"].mean().reset_index()

    if chart_type == "Bar":
        fig = px.bar(pay, x="payment_method", y="TotalPrice",
                     color="TotalPrice", color_continuous_scale="Teal")
    else:
        fig = px.pie(pay, names="payment_method", values="TotalPrice")

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 🎯 DECISION ENGINE
# =====================================================
elif menu == "🎯 Decision Engine":

    st.subheader("🎯 Business Decision Engine")

    chart_type = st.selectbox("Choose Chart Type", ["Bar", "Pie", "Line"])

    col1, col2 = st.columns(2)

    gender = col1.selectbox("Gender", ["All"] + list(df["gender"].unique()))
    category = col1.selectbox("Category", ["All"] + list(df["category"].unique()))
    payment = col2.selectbox("Payment", ["All"] + list(df["payment_method"].unique()))

    price = col1.slider("Price",
                        int(df.price.min()),
                        int(df.price.max()),
                        (int(df.price.min()), int(df.price.max())))

    quantity = col2.slider("Quantity",
                           int(df.quantity.min()),
                           int(df.quantity.max()),
                           (int(df.quantity.min()), int(df.quantity.max())))

    def apply_filters():
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

    if st.button("🚀 Analyze"):

        filtered = apply_filters()

        if filtered.empty:
            st.warning("No data available")
            st.stop()

        # ---------------- ACCURATE RISK ----------------
        filtered["RiskFlag"] = filtered["TotalPrice"] < benchmark

        risk_pct = filtered["RiskFlag"].mean() * 100
        safe_pct = 100 - risk_pct
        avg = filtered["TotalPrice"].mean()

        # ---------------- KPIs ----------------
        c1, c2, c3 = st.columns(3)
        c1.metric("Risk %", f"{risk_pct:.1f}%")
        c2.metric("Safe %", f"{safe_pct:.1f}%")
        c3.metric("Avg Spend", f"₹{avg:.2f}")

        # ---------------- CHART ----------------
        st.subheader("📊 Category Analysis")

        cat = filtered.groupby("category")["TotalPrice"].mean().reset_index()

        if chart_type == "Bar":
            fig = px.bar(cat, x="category", y="TotalPrice",
                         color="TotalPrice",
                         color_continuous_scale="RdYlGn")
        elif chart_type == "Line":
            fig = px.line(cat, x="category", y="TotalPrice")
        else:
            fig = px.pie(cat, names="category", values="TotalPrice")

        st.plotly_chart(fig, use_container_width=True)

        # ---------------- INSIGHTS ----------------
        st.subheader("💡 Insights")

        if len(cat) > 0:
            best = cat.loc[cat["TotalPrice"].idxmax()]["category"]
            worst = cat.loc[cat["TotalPrice"].idxmin()]["category"]

            st.write(f"""
            - 🔴 Risk Transactions: {risk_pct:.1f}%
            - 🟢 Safe Transactions: {safe_pct:.1f}%
            - 🏆 Best Category: {best}
            - ⚠️ Low Performing Category: {worst}

            👉 Interpretation:
            - Higher risk % means more low-value purchases  
            - Best category drives revenue  
            - Low category needs improvement  
            """)
