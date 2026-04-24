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

    # ---- AGE GROUP ----
    if "age" in df.columns:
        df["AgeGroup"] = pd.cut(df["age"],
                               bins=[0, 25, 45, 100],
                               labels=["Young", "Middle", "Senior"])

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
# 🎯 DECISION ENGINE (UPDATED)
# =====================================================
if menu == "🎯 Decision Engine":

    st.subheader("🎯 Business Decision Engine")

    chart_type = st.selectbox("Choose Chart Type", ["Bar", "Pie", "Line"])

    col1, col2 = st.columns(2)

    gender = col1.selectbox("Gender", ["All"] + list(df["gender"].unique()))
    category = col1.selectbox("Category", ["All"] + list(df["category"].unique()))
    payment = col2.selectbox("Payment", ["All"] + list(df["payment_method"].unique()))

    # ✅ AGE FILTER
    if "age" in df.columns:
        age_range = col2.slider("Age Range",
                               int(df.age.min()),
                               int(df.age.max()),
                               (int(df.age.min()), int(df.age.max())))
    else:
        age_range = None

    price = col1.slider("Price",
                        int(df.price.min()),
                        int(df.price.max()),
                        (int(df.price.min()), int(df.price.max())))

    quantity = col2.slider("Quantity",
                           int(df.quantity.min()),
                           int(df.quantity.max()),
                           (int(df.quantity.min()), int(df.quantity.max())))

    # ---------------- FILTER FUNCTION ----------------
    def apply_filters():
        f = df.copy()

        if gender != "All":
            f = f[f["gender"] == gender]

        if category != "All":
            f = f[f["category"] == category]

        if payment != "All":
            f = f[f["payment_method"] == payment]

        if age_range:
            f = f[(f["age"] >= age_range[0]) & (f["age"] <= age_range[1])]

        f = f[(f["price"] >= price[0]) & (f["price"] <= price[1])]
        f = f[(f["quantity"] >= quantity[0]) & (f["quantity"] <= quantity[1])]

        return f

    # ---------------- ANALYZE ----------------
    if st.button("🚀 Analyze"):

        filtered = apply_filters()

        if filtered.empty:
            st.warning("No data available")
            st.stop()

        # ---------------- RISK LOGIC ----------------
        filtered["RiskFlag"] = filtered["TotalPrice"] < benchmark

        risk_pct = filtered["RiskFlag"].mean() * 100
        safe_pct = 100 - risk_pct
        avg = filtered["TotalPrice"].mean()

        # ---------------- KPI ----------------
        c1, c2, c3 = st.columns(3)
        c1.metric("Risk %", f"{risk_pct:.1f}%")
        c2.metric("Safe %", f"{safe_pct:.1f}%")
        c3.metric("Avg Spend", f"₹{avg:.2f}")

        # ---------------- CHART 1 ----------------
        st.subheader("📊 Category Performance")
        cat = filtered.groupby("category")["TotalPrice"].mean().reset_index()

        if chart_type == "Bar":
            fig1 = px.bar(cat, x="category", y="TotalPrice",
                          color="TotalPrice",
                          color_continuous_scale="RdYlGn")
        elif chart_type == "Line":
            fig1 = px.line(cat, x="category", y="TotalPrice")
        else:
            fig1 = px.pie(cat, names="category", values="TotalPrice")

        st.plotly_chart(fig1, use_container_width=True)

        # ---------------- CHART 2 ----------------
        st.subheader("👥 Gender Analysis")
        gen = filtered.groupby("gender")["TotalPrice"].mean().reset_index()

        fig2 = px.bar(gen, x="gender", y="TotalPrice",
                      color="gender",
                      color_discrete_map={"Male": "blue", "Female": "pink"})

        st.plotly_chart(fig2, use_container_width=True)

        # ---------------- CHART 3 (NEW) ----------------
        if "AgeGroup" in filtered.columns:

            st.subheader("🎯 Age Group Analysis")

            age_grp = filtered.groupby("AgeGroup")["TotalPrice"].mean().reset_index()

            fig3 = px.bar(age_grp,
                          x="AgeGroup",
                          y="TotalPrice",
                          color="AgeGroup",
                          color_discrete_map={
                              "Young": "green",
                              "Middle": "orange",
                              "Senior": "red"
                          })

            st.plotly_chart(fig3, use_container_width=True)

        # ---------------- INSIGHTS ----------------
        st.subheader("💡 Insights")

        best = cat.loc[cat["TotalPrice"].idxmax()]["category"]
        worst = cat.loc[cat["TotalPrice"].idxmin()]["category"]

        st.write(f"""
        - 🔴 Risk Transactions: {risk_pct:.1f}%
        - 🟢 Safe Transactions: {safe_pct:.1f}%
        - 🏆 Best Category: {best}
        - ⚠️ Low Category: {worst}

        👉 Age Insight:
        Younger customers usually show lower spending,
        while middle-age customers contribute more revenue.

        👉 Interpretation:
        - High risk = more low-value purchases  
        - Category and age strongly affect performance  
        """)
