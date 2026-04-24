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

# ---------------- TOP MENU ----------------
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

    st.subheader("📊 Category Revenue")
    cat = df.groupby("category")["TotalPrice"].sum().reset_index()
    st.plotly_chart(px.bar(cat, x="category", y="TotalPrice", color="TotalPrice"),
                    use_container_width=True)

# =====================================================
# 👥 CUSTOMERS
# =====================================================
elif menu == "👥 Customers":

    st.subheader("👥 Customer Spending")

    gen = df.groupby("gender")["TotalPrice"].mean().reset_index()

    fig = px.bar(gen, x="gender", y="TotalPrice",
                 color="TotalPrice",
                 text=gen["TotalPrice"].round(1))

    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 📦 PRODUCTS
# =====================================================
elif menu == "📦 Products":

    st.subheader("📦 Product Category Performance")

    cat = df.groupby("category")["TotalPrice"].mean().reset_index()

    st.plotly_chart(px.bar(cat, x="category", y="TotalPrice", color="TotalPrice"),
                    use_container_width=True)

# =====================================================
# 💳 PAYMENT
# =====================================================
elif menu == "💳 Payment":

    st.subheader("💳 Payment Analysis")

    pay = df.groupby("payment_method")["TotalPrice"].mean().reset_index()

    st.plotly_chart(px.bar(pay, x="payment_method", y="TotalPrice", color="TotalPrice"),
                    use_container_width=True)

# =====================================================
# 🎯 DECISION ENGINE
# =====================================================
elif menu == "🎯 Decision Engine":

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

    def compute_risk(data):
        avg = data["TotalPrice"].mean()
        low = (data["TotalPrice"] < benchmark).mean() * 100
        safe = 100 - low
        return low, safe, avg

    if st.button("🚀 Analyze"):

        filtered = apply_filters()

        if filtered.empty:
            st.error("No data for selected filters")
            st.stop()

        risk, safe, avg = compute_risk(filtered)

        # ---------------- KPIs ----------------
        c1, c2, c3 = st.columns(3)
        c1.metric("Risk %", f"{risk:.1f}%")
        c2.metric("Safe %", f"{safe:.1f}%")
        c3.metric("Avg Value", f"₹{avg:.2f}")

        # ---------------- CHART 1 ----------------
        st.subheader("🔍 Safe vs Risk")
        pie = pd.DataFrame({"Type": ["Safe", "Risk"], "Value": [safe, risk]})

        st.plotly_chart(px.pie(pie, names="Type", values="Value",
                              color="Type",
                              color_discrete_map={"Safe": "green", "Risk": "red"},
                              hole=0.5),
                        use_container_width=True)

        # ---------------- CHART 2 ----------------
        st.subheader("📊 Category Performance")

        cat = filtered.groupby("category")["TotalPrice"].mean().reset_index()

        st.plotly_chart(px.bar(cat, x="category", y="TotalPrice",
                               color="TotalPrice",
                               text=cat["TotalPrice"].round(1)),
                        use_container_width=True)

        # ---------------- CHART 3 ----------------
        st.subheader("👥 Gender Comparison")

        gen = filtered.groupby("gender")["TotalPrice"].mean().reset_index()

        st.plotly_chart(px.bar(gen, x="gender", y="TotalPrice",
                               color="TotalPrice",
                               text=gen["TotalPrice"].round(1)),
                        use_container_width=True)

        # ---------------- INSIGHTS ----------------
        st.subheader("💡 Insights & Interpretation")

        high_cat = cat.loc[cat["TotalPrice"].idxmax()]["category"]

        st.write(f"""
        - **Risk Level:** {'High' if risk>60 else 'Medium' if risk>30 else 'Low'}
        - **Low-value Transactions:** {risk:.1f}%
        - **Best Category:** {high_cat}
        - **Average Spending:** ₹{avg:.2f}

        👉 Interpretation:
        - Higher low-value % increases risk  
        - Higher average value improves performance  
        - Category differences show spending behavior  
        """)
