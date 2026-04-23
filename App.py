import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🧠 Retail Business Intelligence Dashboard")

# ---------------- UPLOAD ----------------
file = st.sidebar.file_uploader("📂 Upload Excel File", type=["xlsx"])

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()
    df["TotalPrice"] = df["price"] * df["quantity"]
    return df

if file:

    df = load_data(file)

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

        st.write("### Revenue by Category (Clear View)")
        rev = df.groupby("category")["TotalPrice"].sum().reset_index()
        st.plotly_chart(px.bar(rev, x="category", y="TotalPrice"), use_container_width=True)

    # ================= CUSTOMER =================
    with tab2:
        st.subheader("👥 Customer Insights")

        g = df.groupby("gender")["TotalPrice"].sum().reset_index()
        st.plotly_chart(px.bar(g, x="gender", y="TotalPrice"), use_container_width=True)

        st.write("### Avg Spend")
        st.dataframe(df.groupby("gender")["TotalPrice"].mean())

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

        st.info("Select filters → Click Analyze → Get insights")

        col1, col2 = st.columns(2)

        # -------- FILTERS --------
        gender = col1.selectbox("Gender", ["All"] + list(df["gender"].unique()))
        category = col1.selectbox("Category", ["All"] + list(df["category"].unique()))
        payment = col2.selectbox("Payment Method", ["All"] + list(df["payment_method"].unique()))

        price = col2.slider("Price Range", int(df["price"].min()), int(df["price"].max()), (100, 2000))
        quantity = st.slider("Quantity Range", int(df["quantity"].min()), int(df["quantity"].max()), (1, 5))

        # -------- BUTTON CONTROL --------
        if "run" not in st.session_state:
            st.session_state.run = False

        if st.button("🚀 Analyze"):
            st.session_state.run = True

        if st.session_state.run:

            filtered = df.copy()

            # -------- APPLY FILTERS --------
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
                st.error("No data found for selected filters")

            else:
                st.subheader("📊 Result")

                total = filtered["TotalPrice"].sum()
                avg = df["TotalPrice"].mean()

                st.metric("Filtered Revenue", f"₹{total:,.0f}")

                # VALUE
                if total > avg * len(filtered):
                    st.success("💰 High Value Segment")
                elif total > avg * len(filtered) * 0.7:
                    st.warning("⚠️ Medium Value Segment")
                else:
                    st.error("🚨 Low Value Segment")

                # RISK
                low_value_pct = (filtered["TotalPrice"] < avg).mean() * 100

                if low_value_pct < 40:
                    st.success("✅ LOW RISK")
                elif low_value_pct < 70:
                    st.warning("⚠️ MEDIUM RISK")
                else:
                    st.error("🚨 HIGH RISK")

                # -------- CHARTS (NEW) --------
                st.subheader("📈 Visual Insights")

                colA, colB = st.columns(2)

                # Revenue by Category
                with colA:
                    cat_rev = filtered.groupby("category")["TotalPrice"].sum().reset_index()
                    st.plotly_chart(px.bar(cat_rev, x="category", y="TotalPrice", title="Revenue by Category"), use_container_width=True)

                # Gender Spending
                with colB:
                    gen_rev = filtered.groupby("gender")["TotalPrice"].sum().reset_index()
                    st.plotly_chart(px.pie(gen_rev, names="gender", values="TotalPrice", title="Gender Contribution"))

                # Payment Method
                pay = filtered["payment_method"].value_counts().reset_index()
                pay.columns = ["method", "count"]
                st.plotly_chart(px.bar(pay, x="method", y="count", title="Payment Distribution"), use_container_width=True)

                # Price vs Quantity
                st.plotly_chart(px.scatter(filtered, x="price", y="quantity", color="category",
                                           title="Price vs Quantity"), use_container_width=True)

                # -------- PROBLEM --------
                st.subheader("⚠️ Problem")

                if low_value_pct > 60:
                    st.write("- Too many low-value transactions")

                if filtered["quantity"].mean() < df["quantity"].mean():
                    st.write("- Customers buying less quantity")

                if filtered["price"].mean() < df["price"].mean():
                    st.write("- Low price products dominating")

                # -------- RECOMMENDATION --------
                st.subheader("💡 Recommendation")

                if low_value_pct > 60:
                    st.write("- Improve product value or pricing")

                if filtered["quantity"].mean() < df["quantity"].mean():
                    st.write("- Offer combo deals")

                if filtered["price"].mean() < df["price"].mean():
                    st.write("- Promote premium products")
else:
    st.warning("📂 Upload dataset to begin")