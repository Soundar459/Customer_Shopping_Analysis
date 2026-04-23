import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🧠 Retail Business Intelligence Dashboard")

# ---------------- DATA LOAD ----------------
@st.cache_data
def load_data():
    df = pd.read_excel("customer_shopping_data1.xlsx")
    df.columns = df.columns.str.strip()
    df["TotalPrice"] = df["price"] * df["quantity"]
    return df

try:
    df = load_data()
    st.success("✅ Dataset Loaded")
except:
    st.error("❌ Dataset not found")
    st.stop()

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Overview",
    "👥 Customers",
    "🛍️ Products",
    "💳 Payment",
    "🎯 Decision Engine"
])

# ================= OVERVIEW =================
with tab1:
    st.subheader("📊 Business Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Revenue", f"₹{df['TotalPrice'].sum():,.0f}")
    col2.metric("Total Orders", len(df))
    col3.metric("Avg Order Value", f"₹{df['TotalPrice'].mean():.2f}")

    rev = df.groupby("category")["TotalPrice"].sum().reset_index()
    st.plotly_chart(px.bar(rev, x="category", y="TotalPrice"), use_container_width=True)

# ================= CUSTOMER =================
with tab2:
    st.subheader("👥 Customer Insights")

    g = df.groupby("gender")["TotalPrice"].sum().reset_index()
    st.plotly_chart(px.bar(g, x="gender", y="TotalPrice"), use_container_width=True)

# ================= PRODUCTS =================
with tab3:
    st.subheader("🛍️ Product Insights")

    c = df.groupby("category")["quantity"].sum().reset_index()
    st.plotly_chart(px.bar(c, x="category", y="quantity"), use_container_width=True)

# ================= PAYMENT =================
with tab4:
    st.subheader("💳 Payment Insights")

    p = df["payment_method"].value_counts().reset_index()
    p.columns = ["method", "count"]
    st.plotly_chart(px.bar(p, x="method", y="count"), use_container_width=True)

# ================= DECISION ENGINE =================
with tab5:

    st.subheader("🎯 Business Decision Engine")
    st.info("Select filters → Click Analyze → Get clear risk insights")

    col1, col2 = st.columns(2)

    gender = col1.selectbox("Gender", ["All"] + list(df["gender"].unique()))
    category = col1.selectbox("Category", ["All"] + list(df["category"].unique()))
    payment = col2.selectbox("Payment Method", ["All"] + list(df["payment_method"].unique()))

    price = col2.slider("Price Range",
                        int(df["price"].min()),
                        int(df["price"].max()),
                        (int(df["price"].min()), int(df["price"].max())))

    quantity = st.slider("Quantity Range",
                         int(df["quantity"].min()),
                         int(df["quantity"].max()),
                         (int(df["quantity"].min()), int(df["quantity"].max())))

    if st.button("🚀 Analyze"):

        filtered = df.copy()

        if gender != "All":
            filtered = filtered[filtered["gender"] == gender]

        if category != "All":
            filtered = filtered[filtered["category"] == category]

        if payment != "All":
            filtered = filtered[filtered["payment_method"] == payment]

        filtered = filtered[
            (filtered["price"] >= price[0]) &
            (filtered["price"] <= price[1]) &
            (filtered["quantity"] >= quantity[0]) &
            (filtered["quantity"] <= quantity[1])
        ]

        if len(filtered) == 0:
            st.error("❌ No data found")

        else:
            avg_total = df["TotalPrice"].mean()

            # -------- RISK FLAG --------
            filtered["RiskFlag"] = filtered["TotalPrice"] < avg_total

            risk_pct = filtered["RiskFlag"].mean() * 100
            safe_pct = 100 - risk_pct

            # -------- RESULT --------
            st.subheader("📊 Overall Risk Result")

            if risk_pct < 40:
                st.success("✅ LOW RISK")
            elif risk_pct < 70:
                st.warning("⚠️ MEDIUM RISK")
            else:
                st.error("🚨 HIGH RISK")

            # -------- PIE --------
            risk_data = pd.DataFrame({
                "Status": ["Safe", "Risk"],
                "Percentage": [safe_pct, risk_pct]
            })

            st.plotly_chart(
                px.pie(risk_data, names="Status", values="Percentage",
                       color="Status",
                       color_discrete_map={"Safe": "green", "Risk": "red"}),
                use_container_width=True
            )

            st.write(f"🟢 Safe: {safe_pct:.1f}%")
            st.write(f"🔴 Risk: {risk_pct:.1f}%")

            # ================= NEW CLEAR ANALYTICS =================

            # -------- CATEGORY RISK --------
            st.subheader("📊 Risk by Category")

            cat = filtered.groupby("category")["RiskFlag"].mean().reset_index()
            cat["Risk %"] = cat["RiskFlag"] * 100

            st.plotly_chart(
                px.bar(cat, x="category", y="Risk %",
                       color="Risk %",
                       color_continuous_scale=["green", "red"]),
                use_container_width=True
            )

            # -------- GENDER RISK --------
            st.subheader("👥 Risk by Gender")

            gen = filtered.groupby("gender")["RiskFlag"].mean().reset_index()
            gen["Risk %"] = gen["RiskFlag"] * 100

            st.plotly_chart(
                px.bar(gen, x="gender", y="Risk %",
                       color="Risk %",
                       color_continuous_scale=["green", "red"]),
                use_container_width=True
            )

            # -------- INSIGHT --------
            st.subheader("📌 Key Insight")

            worst_cat = cat.sort_values("Risk %", ascending=False).iloc[0]["category"]
            st.write(f"⚠️ Highest risk category: {worst_cat}")

            # -------- PROBLEM --------
            st.subheader("⚠️ Problem")

            if risk_pct > 60:
                st.write("- Too many low-value transactions")

            if filtered["quantity"].mean() < df["quantity"].mean():
                st.write("- Customers buying low quantity")

            # -------- RECOMMENDATION --------
            st.subheader("💡 Recommendation")

            if risk_pct > 60:
                st.write("- Improve pricing strategy")

            if filtered["quantity"].mean() < df["quantity"].mean():
                st.write("- Offer combo deals")
