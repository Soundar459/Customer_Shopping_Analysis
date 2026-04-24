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
# 🏠 OVERVIEW
# =====================================================
if menu == "🏠 Overview":

    st.subheader("📊 Overview Dashboard")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"₹{df['TotalPrice'].sum():,.0f}")
    col2.metric("Transactions", len(df))
    col3.metric("Avg Value", f"₹{df['TotalPrice'].mean():.2f}")

    chart = st.selectbox("Choose Chart", ["Bar", "Pie"])

    cat = df.groupby("category")["TotalPrice"].sum().reset_index()

    if not cat.empty:
        if chart == "Bar":
            fig = px.bar(cat, x="category", y="TotalPrice",
                         color="TotalPrice", color_continuous_scale="Blues")
        else:
            fig = px.pie(cat, names="category", values="TotalPrice")

        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 👥 CUSTOMERS
# =====================================================
elif menu == "👥 Customers":

    st.subheader("👥 Customer Analysis")

    chart = st.selectbox("Choose Chart", ["Bar", "Pie"])

    gen = df.groupby("gender")["TotalPrice"].mean().reset_index()

    if not gen.empty:
        if chart == "Bar":
            fig = px.bar(gen, x="gender", y="TotalPrice",
                         color="gender",
                         color_discrete_map={"Male": "blue", "Female": "pink"})
        else:
            fig = px.pie(gen, names="gender", values="TotalPrice")

        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 📦 PRODUCTS
# =====================================================
elif menu == "📦 Products":

    st.subheader("📦 Product Performance")

    chart = st.selectbox("Choose Chart", ["Bar", "Pie", "Line"])

    cat = df.groupby("category")["TotalPrice"].mean().reset_index()

    if not cat.empty:
        if chart == "Bar":
            fig = px.bar(cat, x="category", y="TotalPrice",
                         color="TotalPrice", color_continuous_scale="Viridis")
        elif chart == "Line":
            fig = px.line(cat, x="category", y="TotalPrice", markers=True)
        else:
            fig = px.pie(cat, names="category", values="TotalPrice")

        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 💳 PAYMENT
# =====================================================
elif menu == "💳 Payment":

    st.subheader("💳 Payment Analysis")

    chart = st.selectbox("Choose Chart", ["Bar", "Pie"])

    pay = df.groupby("payment_method")["TotalPrice"].mean().reset_index()

    if not pay.empty:
        if chart == "Bar":
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

    chart = st.selectbox("Choose Chart", ["Bar", "Pie", "Line"])

    col1, col2 = st.columns(2)

    gender = col1.selectbox("Gender", ["All"] + list(df["gender"].unique()))
    category = col1.selectbox("Category", ["All"] + list(df["category"].unique()))
    payment = col2.selectbox("Payment", ["All"] + list(df["payment_method"].unique()))

    # AGE FILTER
    age_range = None
    if "age" in df.columns:
        age_range = col2.slider("Age Range",
                               int(df.age.min()),
                               int(df.age.max()),
                               (int(df.age.min()), int(df.age.max())))

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

        if age_range:
            f = f[(f["age"] >= age_range[0]) & (f["age"] <= age_range[1])]

        f = f[(f["price"] >= price[0]) & (f["price"] <= price[1])]
        f = f[(f["quantity"] >= quantity[0]) & (f["quantity"] <= quantity[1])]

        return f

    if st.button("🚀 Analyze"):

        filtered = apply_filters()

        if filtered.empty:
            st.warning("No data available")
            st.stop()

        filtered["RiskFlag"] = filtered["TotalPrice"] < benchmark

        risk = filtered["RiskFlag"].mean() * 100
        safe = 100 - risk
        avg = filtered["TotalPrice"].mean()

        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Risk %", f"{risk:.1f}%")
        c2.metric("Safe %", f"{safe:.1f}%")
        c3.metric("Avg Spend", f"₹{avg:.2f}")

        # CATEGORY CHART
        st.subheader("📊 Category Analysis")

        cat = filtered.groupby("category")["TotalPrice"].mean().reset_index()

        if not cat.empty:
            if chart == "Bar":
                fig = px.bar(cat, x="category", y="TotalPrice",
                             color="TotalPrice",
                             color_continuous_scale="RdYlGn")
            elif chart == "Line":
                fig = px.line(cat, x="category", y="TotalPrice", markers=True)
            else:
                fig = px.pie(cat, names="category", values="TotalPrice")

            st.plotly_chart(fig, use_container_width=True)

        # AGE CHART
        if "AgeGroup" in filtered.columns:
            st.subheader("👤 Age Analysis")

            age_df = filtered.groupby("AgeGroup")["TotalPrice"].mean().reset_index()

            fig2 = px.bar(age_df, x="AgeGroup", y="TotalPrice",
                          color="AgeGroup")

            st.plotly_chart(fig2, use_container_width=True)

        # INSIGHTS
        st.subheader("💡 Insights")

        best = cat.loc[cat["TotalPrice"].idxmax()]["category"]
        worst = cat.loc[cat["TotalPrice"].idxmin()]["category"]

        st.write(f"""
        - Risk: {risk:.1f}%
        - Safe: {safe:.1f}%
        - Best Category: {best}
        - Low Category: {worst}

        👉 Interpretation:
        - Higher risk → more low-value purchases  
        - Best category drives revenue  
        - Age and category influence spending  
        """)
