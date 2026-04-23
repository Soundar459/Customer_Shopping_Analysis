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

# ================= DECISION ENGINE =================
with tab5:

    st.subheader("🎯 Business Decision Engine")
    st.info("Select filters → Click Analyze → Get clear insights")

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

        # FILTERS
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

            # 🔥 IMPORTANT FIX → use FILTERED average (not full dataset)
            avg_total = filtered["TotalPrice"].mean()

            filtered["RiskFlag"] = filtered["TotalPrice"] < avg_total

            risk_pct = filtered["RiskFlag"].mean() * 100
            safe_pct = 100 - risk_pct

            # ================= RESULT =================
            st.subheader("📊 Overall Result")

            if risk_pct < 40:
                st.success("✅ LOW RISK SEGMENT")
            elif risk_pct < 70:
                st.warning("⚠️ MEDIUM RISK SEGMENT")
            else:
                st.error("🚨 HIGH RISK SEGMENT")

            # PIE
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

            st.write(f"🟢 Safe Customers: {safe_pct:.1f}%")
            st.write(f"🔴 Risk Customers: {risk_pct:.1f}%")

            # ================= CATEGORY =================
            st.subheader("📊 Category Analysis")

            cat = filtered.groupby("category").agg({
                "TotalPrice": "mean"
            }).reset_index()

            cat["Risk %"] = ((avg_total - cat["TotalPrice"]) / avg_total) * 100
            cat["Risk %"] = cat["Risk %"].clip(lower=0)

            fig1 = px.bar(cat, x="category", y="Risk %",
                          color="Risk %",
                          color_continuous_scale=["green", "red"],
                          text="Risk %")

            fig1.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig1, use_container_width=True)

            # EXPLANATION
            worst_cat = cat.sort_values("Risk %", ascending=False).iloc[0]
            st.info(f"""
📌 Category Insight:
- Highest Risk Category: {worst_cat['category']}
- Risk: {worst_cat['Risk %']:.1f}%
👉 This means this category generates lower revenue compared to average.
""")

            # ================= GENDER =================
            st.subheader("👥 Gender Analysis")

            gen = filtered.groupby("gender").agg({
                "TotalPrice": "mean"
            }).reset_index()

            gen["Risk %"] = ((avg_total - gen["TotalPrice"]) / avg_total) * 100
            gen["Risk %"] = gen["Risk %"].clip(lower=0)

            fig2 = px.bar(gen, x="gender", y="Risk %",
                          color="Risk %",
                          color_continuous_scale=["green", "red"],
                          text="Risk %")

            fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)

            worst_gender = gen.sort_values("Risk %", ascending=False).iloc[0]

            st.info(f"""
📌 Gender Insight:
- Higher Risk Group: {worst_gender['gender']}
- Risk: {worst_gender['Risk %']:.1f}%
👉 This group spends less compared to others.
""")

            # ================= FINAL INSIGHT =================
            st.subheader("💡 Final Business Insight")

            st.write(f"""
- Overall Risk Level: {risk_pct:.1f}%
- Major Issue: Low value transactions in {worst_cat['category']}
- Affected Customer Group: {worst_gender['gender']}

👉 Business should focus on improving pricing, offers and engagement in these segments.
""")
