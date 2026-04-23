import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("🧠 Retail Business Intelligence Dashboard")

# ---------- LOAD DATA ----------
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
    col1.metric("Total Revenue", f"₹{df['TotalPrice'].sum():,.0f}")
    col2.metric("Total Orders", len(df))
    col3.metric("Avg Order Value", f"₹{df['TotalPrice'].mean():.0f}")

    chart = df.groupby("category")["TotalPrice"].sum().reset_index()
    st.plotly_chart(px.bar(chart, x="category", y="TotalPrice"), use_container_width=True)

# ---------- DECISION ENGINE ----------
with tab5:

    st.subheader("🎯 Smart Decision Engine")
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

        # ---------- FILTER ----------
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
            st.error("❌ No data found")
            st.stop()

        # ---------- RISK LOGIC ----------
        avg_total = filtered["TotalPrice"].mean()
        filtered["RiskFlag"] = filtered["TotalPrice"] < avg_total

        risk_pct = filtered["RiskFlag"].mean() * 100
        safe_pct = 100 - risk_pct

        def risk_label(x):
            if x < 40:
                return "Low"
            elif x < 70:
                return "Medium"
            else:
                return "High"

        overall_level = risk_label(risk_pct)

        # ---------- KPI ----------
        colA, colB, colC = st.columns(3)
        colA.metric("Risk %", f"{risk_pct:.1f}%")
        colB.metric("Safe %", f"{safe_pct:.1f}%")
        colC.metric("Risk Level", overall_level)

        # ---------- GAUGE CHART (UNIQUE 🔥) ----------
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_pct,
            title={'text': "Overall Risk"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "red"},
                'steps': [
                    {'range': [0, 40], 'color': 'green'},
                    {'range': [40, 70], 'color': 'orange'},
                    {'range': [70, 100], 'color': 'red'}
                ],
            }
        ))

        st.plotly_chart(fig_gauge, use_container_width=True)

        # ---------- DONUT CHART ----------
        pie = pd.DataFrame({
            "Type": ["Safe", "Risk"],
            "Value": [safe_pct, risk_pct]
        })

        fig_pie = px.pie(pie, names="Type", values="Value",
                         hole=0.5,
                         color="Type",
                         color_discrete_map={"Safe": "green", "Risk": "red"})

        st.plotly_chart(fig_pie, use_container_width=True)

        # ---------- CATEGORY ANALYSIS ----------
        st.subheader("📊 Category Risk Analysis")

        cat = filtered.groupby("category").apply(
            lambda x: (x["TotalPrice"] < avg_total).mean() * 100
        ).reset_index(name="Risk %")

        cat["Level"] = cat["Risk %"].apply(risk_label)

        st.plotly_chart(
            px.bar(cat, x="category", y="Risk %",
                   color="Level",
                   text=cat["Risk %"].round(2),
                   color_discrete_map={
                       "Low": "green",
                       "Medium": "orange",
                       "High": "red"
                   }),
            use_container_width=True
        )

        if len(cat) > 1:
            worst_cat = cat.sort_values("Risk %", ascending=False).iloc[0]

            st.info(f"""
📌 Category Insight  
- Highest Risk Category: {worst_cat['category']}  
- Risk: {worst_cat['Risk %']:.1f}%  
👉 This category contributes more low-value transactions.
""")

        # ---------- GENDER ANALYSIS ----------
        st.subheader("👥 Gender Risk Analysis")

        gen = filtered.groupby("gender").apply(
            lambda x: (x["TotalPrice"] < avg_total).mean() * 100
        ).reset_index(name="Risk %")

        gen["Level"] = gen["Risk %"].apply(risk_label)

        st.plotly_chart(
            px.bar(gen, x="gender", y="Risk %",
                   color="Level",
                   text=gen["Risk %"].round(2),
                   color_discrete_map={
                       "Low": "green",
                       "Medium": "orange",
                       "High": "red"
                   }),
            use_container_width=True
        )

        if len(gen) > 1:
            worst_gen = gen.sort_values("Risk %", ascending=False).iloc[0]

            st.info(f"""
📌 Gender Insight  
- Higher Risk Group: {worst_gen['gender']}  
- Risk: {worst_gen['Risk %']:.1f}%  
👉 This group has lower average spending.
""")

        # ---------- FINAL INSIGHT ----------
        st.subheader("💡 Final Business Insight")

        st.write(f"""
- Overall Risk: {risk_pct:.1f}% ({overall_level})  
- Risk is calculated based on transaction value vs average  
- Higher risk means more low-value purchases  

👉 Focus areas:
- Improve pricing strategy  
- Encourage higher quantity purchase  
- Target low-performing segments  
""")
