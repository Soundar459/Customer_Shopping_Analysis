import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🧠 Retail Business Intelligence Dashboard")

# ---------- LOAD ----------
@st.cache_data
def load_data():
    df = pd.read_excel("customer_shopping_data1.xlsx")
    df.columns = df.columns.str.strip()
    df["TotalPrice"] = df["price"] * df["quantity"]
    return df

df = load_data()

# ---------- TABS ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Overview", "👥 Customers", "🛍️ Products", "💳 Payment", "🎯 Decision Engine"
])

# ---------- OVERVIEW ----------
with tab1:
    st.subheader("📊 Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("Revenue", f"₹{df['TotalPrice'].sum():,.0f}")
    col2.metric("Orders", len(df))
    col3.metric("Avg Order", f"₹{df['TotalPrice'].mean():.0f}")

    chart = df.groupby("category")["TotalPrice"].sum().reset_index()
    st.plotly_chart(px.bar(chart, x="category", y="TotalPrice"), use_container_width=True)

# ---------- DECISION ENGINE ----------
with tab5:

    st.subheader("🎯 Decision Engine")

    col1, col2 = st.columns(2)

    gender = col1.selectbox("Gender", ["All"] + list(df["gender"].unique()))
    category = col1.selectbox("Category", ["All"] + list(df["category"].unique()))
    payment = col2.selectbox("Payment", ["All"] + list(df["payment_method"].unique()))

    price = col2.slider("Price",
                        int(df["price"].min()),
                        int(df["price"].max()),
                        (int(df["price"].min()), int(df["price"].max())))

    quantity = st.slider("Quantity",
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

        if filtered.empty:
            st.error("No data found")
            st.stop()

        # ---------- NEW CORRECT RISK ----------
        avg_total = filtered["TotalPrice"].mean()
        filtered["RiskFlag"] = filtered["TotalPrice"] < avg_total

        risk_pct = filtered["RiskFlag"].mean() * 100
        safe_pct = 100 - risk_pct

        # ---------- RESULT ----------
        st.subheader("📊 Overall Result")

        if risk_pct < 40:
            st.success("LOW RISK")
        elif risk_pct < 70:
            st.warning("MEDIUM RISK")
        else:
            st.error("HIGH RISK")

        pie = pd.DataFrame({
            "Type": ["Safe", "Risk"],
            "Value": [safe_pct, risk_pct]
        })

        st.plotly_chart(
            px.pie(pie, names="Type", values="Value",
                   color="Type",
                   color_discrete_map={"Safe": "green", "Risk": "red"}),
            use_container_width=True
        )

        st.write(f"Safe: {safe_pct:.1f}%")
        st.write(f"Risk: {risk_pct:.1f}%")

        # ---------- CATEGORY ANALYSIS ----------
        st.subheader("📊 Category Risk")

        cat = filtered.groupby("category").apply(
            lambda x: (x["TotalPrice"] < avg_total).mean() * 100
        ).reset_index(name="Risk %")

        st.plotly_chart(
            px.bar(cat, x="category", y="Risk %",
                   color="Risk %",
                   color_continuous_scale=["green", "red"],
                   text="Risk %"),
            use_container_width=True
        )

        if len(cat) > 1:
            worst_cat = cat.sort_values("Risk %", ascending=False).iloc[0]

            st.info(f"""
Category Insight:
- Highest Risk Category: {worst_cat['category']}
- Risk: {worst_cat['Risk %']:.1f}%
""")
        else:
            st.info("Only one category selected — no comparison possible")

        # ---------- GENDER ANALYSIS ----------
        st.subheader("👥 Gender Risk")

        gen = filtered.groupby("gender").apply(
            lambda x: (x["TotalPrice"] < avg_total).mean() * 100
        ).reset_index(name="Risk %")

        st.plotly_chart(
            px.bar(gen, x="gender", y="Risk %",
                   color="Risk %",
                   color_continuous_scale=["green", "red"],
                   text="Risk %"),
            use_container_width=True
        )

        if len(gen) > 1:
            worst_gen = gen.sort_values("Risk %", ascending=False).iloc[0]

            st.info(f"""
Gender Insight:
- Higher Risk Group: {worst_gen['gender']}
- Risk: {worst_gen['Risk %']:.1f}%
""")
        else:
            st.info("Only one gender selected — no comparison possible")

        # ---------- FINAL ----------
        st.subheader("💡 Final Insight")

        st.write(f"""
- Risk Level: {risk_pct:.1f}%
- This result is based on transaction values compared to average.
- Higher risk means more low-value transactions.
""")
