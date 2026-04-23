import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("🧠 Retail Business Intelligence Dashboard")

# ---------------- DATA LOAD ----------------
REQUIRED_COLS = {
    "invoice_no", "customer_id", "gender", "age", "category",
    "quantity", "price", "payment_method", "invoice_date", "shopping_mall"
}

@st.cache_data
def load_data():
    df = pd.read_excel("customer_shopping_data1.xlsx")
    df.columns = df.columns.str.strip()

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in Excel: {sorted(missing)}")

    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df["TotalPrice"] = df["price"] * df["quantity"]

    # Small helper fields for better visuals
    df["month"] = df["invoice_date"].dt.to_period("M").astype(str)
    return df

try:
    df = load_data()
    st.success("✅ Dataset Loaded")
except Exception as e:
    st.error(f"❌ Dataset not found or invalid: {e}")
    st.stop()

# ---------------- HELPERS ----------------
def risk_level(score: float) -> str:
    if score < 30:
        return "Low"
    elif score < 60:
        return "Medium"
    return "High"

def risk_color(level: str) -> str:
    return {"Low": "green", "Medium": "orange", "High": "red"}.get(level, "gray")

def apply_filters(
    data: pd.DataFrame,
    gender_sel: str = "All",
    category_sel: str = "All",
    payment_sel: str = "All",
    price_range=None,
    quantity_range=None,
    mall_sel: str = "All",
    ignore=None
) -> pd.DataFrame:
    ignore = set(ignore or [])
    f = data.copy()

    if gender_sel != "All" and "gender" not in ignore:
        f = f[f["gender"] == gender_sel]

    if category_sel != "All" and "category" not in ignore:
        f = f[f["category"] == category_sel]

    if payment_sel != "All" and "payment_method" not in ignore:
        f = f[f["payment_method"] == payment_sel]

    if mall_sel != "All" and "shopping_mall" not in ignore:
        f = f[f["shopping_mall"] == mall_sel]

    if price_range is not None:
        f = f[(f["price"] >= price_range[0]) & (f["price"] <= price_range[1])]

    if quantity_range is not None:
        f = f[(f["quantity"] >= quantity_range[0]) & (f["quantity"] <= quantity_range[1])]

    return f

def compute_risk_metrics(data: pd.DataFrame, benchmark: float) -> dict:
    """
    Risk is based on the dataset median benchmark.
    - low_value_share: % of transactions below benchmark
    - avg_penalty: penalty when avg is below benchmark
    - median_penalty: penalty when median is below benchmark
    """
    if data.empty:
        return {
            "count": 0,
            "revenue": 0.0,
            "avg_value": 0.0,
            "median_value": 0.0,
            "low_value_share": 0.0,
            "safe_share": 0.0,
            "risk_score": 0.0,
            "risk_level": "Low",
        }

    avg_value = float(data["TotalPrice"].mean())
    median_value = float(data["TotalPrice"].median())
    low_value_share = float((data["TotalPrice"] < benchmark).mean() * 100)
    safe_share = 100.0 - low_value_share

    avg_penalty = max(0.0, 100.0 * (1.0 - (avg_value / benchmark))) if benchmark > 0 else 0.0
    median_penalty = max(0.0, 100.0 * (1.0 - (median_value / benchmark))) if benchmark > 0 else 0.0

    # Weighted score: low-value share matters most, but average & median add context.
    risk_score = (0.7 * low_value_share) + (0.2 * avg_penalty) + (0.1 * median_penalty)
    risk_score = float(np.clip(risk_score, 0, 100))

    return {
        "count": int(len(data)),
        "revenue": float(data["TotalPrice"].sum()),
        "avg_value": avg_value,
        "median_value": median_value,
        "low_value_share": low_value_share,
        "safe_share": safe_share,
        "risk_score": risk_score,
        "risk_level": risk_level(risk_score),
    }

def build_group_risk_table(
    data: pd.DataFrame,
    group_col: str,
    benchmark: float
) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame(columns=[
            group_col, "Transactions", "Revenue", "Avg Value", "Median Value",
            "Low Value %", "Risk Score", "Risk Level"
        ])

    rows = []
    for key, grp in data.groupby(group_col):
        metrics = compute_risk_metrics(grp, benchmark)
        rows.append({
            group_col: key,
            "Transactions": metrics["count"],
            "Revenue": metrics["revenue"],
            "Avg Value": metrics["avg_value"],
            "Median Value": metrics["median_value"],
            "Low Value %": metrics["low_value_share"],
            "Risk Score": metrics["risk_score"],
            "Risk Level": metrics["risk_level"],
        })

    out = pd.DataFrame(rows).sort_values("Risk Score", ascending=False).reset_index(drop=True)
    return out

# Benchmark for all risk logic
benchmark_median = float(df["TotalPrice"].median())

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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{df['TotalPrice'].sum():,.0f}")
    c2.metric("Total Orders", len(df))
    c3.metric("Avg Order Value", f"₹{df['TotalPrice'].mean():.2f}")
    c4.metric("Median Order Value", f"₹{df['TotalPrice'].median():.2f}")

    st.caption(f"Benchmark used in risk analysis = dataset median transaction value ₹{benchmark_median:.2f}")

    colA, colB = st.columns(2)

    with colA:
        st.write("### Revenue by Category")
        rev = df.groupby("category", as_index=False)["TotalPrice"].sum().sort_values("TotalPrice", ascending=False)
        fig = px.bar(rev, x="category", y="TotalPrice", text="TotalPrice", title="Revenue Contribution by Category")
        fig.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    with colB:
        st.write("### Revenue by Shopping Mall")
        mall_rev = df.groupby("shopping_mall", as_index=False)["TotalPrice"].sum().sort_values("TotalPrice", ascending=False)
        fig = px.bar(mall_rev, x="shopping_mall", y="TotalPrice", text="TotalPrice", title="Revenue by Shopping Mall")
        fig.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    st.write("### Monthly Revenue Trend")
    monthly = df.dropna(subset=["month"]).groupby("month", as_index=False)["TotalPrice"].sum()
    if not monthly.empty:
        fig = px.line(monthly, x="month", y="TotalPrice", markers=True, title="Revenue Trend by Month")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Invoice date data is not sufficient for monthly trend.")

# ================= CUSTOMERS =================
with tab2:
    st.subheader("👥 Customer Insights")

    c1, c2 = st.columns(2)

    with c1:
        gender_rev = df.groupby("gender", as_index=False)["TotalPrice"].sum()
        fig = px.bar(gender_rev, x="gender", y="TotalPrice", text="TotalPrice", title="Revenue by Gender")
        fig.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        age_band = pd.cut(
            df["age"],
            bins=[0, 20, 30, 40, 50, 60, 70],
            labels=["0-20", "21-30", "31-40", "41-50", "51-60", "61-70"],
            include_lowest=True
        )
        age_rev = df.assign(AgeBand=age_band).groupby("AgeBand", observed=True, as_index=False)["TotalPrice"].sum()
        fig = px.bar(age_rev, x="AgeBand", y="TotalPrice", text="TotalPrice", title="Revenue by Age Band")
        fig.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    st.write("### Top Customers by Revenue")
    top_customers = df.groupby("customer_id", as_index=False)["TotalPrice"].sum().sort_values("TotalPrice", ascending=False).head(10)
    fig = px.bar(top_customers, x="customer_id", y="TotalPrice", text="TotalPrice", title="Top 10 Customers")
    fig.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# ================= PRODUCTS =================
with tab3:
    st.subheader("🛍️ Product Insights")

    c1, c2 = st.columns(2)

    with c1:
        qty = df.groupby("category", as_index=False)["quantity"].sum().sort_values("quantity", ascending=False)
        fig = px.bar(qty, x="category", y="quantity", text="quantity", title="Quantity Sold by Category")
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        cat_rev = df.groupby("category", as_index=False)["TotalPrice"].sum().sort_values("TotalPrice", ascending=False)
        fig = px.pie(cat_rev, names="category", values="TotalPrice", hole=0.45, title="Revenue Share by Category")
        st.plotly_chart(fig, use_container_width=True)

    st.write("### Category Summary Table")
    st.dataframe(
        df.groupby("category", as_index=False).agg(
            Orders=("invoice_no", "count"),
            Revenue=("TotalPrice", "sum"),
            Avg_Value=("TotalPrice", "mean")
        ).sort_values("Revenue", ascending=False),
        use_container_width=True
    )

# ================= PAYMENT =================
with tab4:
    st.subheader("💳 Payment Insights")

    c1, c2 = st.columns(2)

    with c1:
        pm = df["payment_method"].value_counts().reset_index()
        pm.columns = ["payment_method", "count"]
        fig = px.bar(pm, x="payment_method", y="count", text="count", title="Payment Method Usage")
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        mall_pay = df.groupby(["shopping_mall", "payment_method"], as_index=False)["TotalPrice"].sum()
        fig = px.bar(
            mall_pay,
            x="shopping_mall",
            y="TotalPrice",
            color="payment_method",
            barmode="stack",
            title="Payment-wise Revenue by Mall"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.write("### Payment Summary")
    st.dataframe(
        df.groupby("payment_method", as_index=False).agg(
            Orders=("invoice_no", "count"),
            Revenue=("TotalPrice", "sum"),
            Avg_Value=("TotalPrice", "mean")
        ).sort_values("Revenue", ascending=False),
        use_container_width=True
    )

# ================= DECISION ENGINE =================
with tab5:
    st.subheader("🎯 Business Decision Engine")
    st.info("Select filters → Click Analyze → Get clear insights")

    # Filters
    col1, col2 = st.columns(2)

    gender = col1.selectbox("Gender", ["All"] + sorted(df["gender"].dropna().unique().tolist()))
    category = col1.selectbox("Category", ["All"] + sorted(df["category"].dropna().unique().tolist()))
    payment = col2.selectbox("Payment Method", ["All"] + sorted(df["payment_method"].dropna().unique().tolist()))
    mall = col2.selectbox("Shopping Mall", ["All"] + sorted(df["shopping_mall"].dropna().unique().tolist()))

    price = col1.slider(
        "Price Range",
        int(df["price"].min()),
        int(df["price"].max()),
        (int(df["price"].min()), int(df["price"].max()))
    )

    quantity = col2.slider(
        "Quantity Range",
        int(df["quantity"].min()),
        int(df["quantity"].max()),
        (int(df["quantity"].min()), int(df["quantity"].max()))
    )

    if st.button("🚀 Analyze"):
        with st.spinner("Analyzing selected business scenario..."):
            selected = apply_filters(
                df,
                gender_sel=gender,
                category_sel=category,
                payment_sel=payment,
                price_range=price,
                quantity_range=quantity,
                mall_sel=mall
            )

            if selected.empty:
                st.error("❌ No data found for selected filters")
                st.stop()

            # -------- OVERALL METRICS FOR SELECTED SEGMENT --------
            overall = compute_risk_metrics(selected, benchmark_median)

            # KPI cards
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Transactions", f"{overall['count']:,}")
            k2.metric("Segment Revenue", f"₹{overall['revenue']:,.0f}")
            k3.metric("Avg Transaction", f"₹{overall['avg_value']:.2f}", delta=f"vs benchmark ₹{benchmark_median:.2f}")
            k4.metric("Risk Score", f"{overall['risk_score']:.1f}/100")

            st.progress(int(round(overall["risk_score"])))

            # -------- ANIMATED STYLE GAUGE --------
            st.subheader("📊 Overall Risk Result")

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=overall["risk_score"],
                delta={"reference": 50, "increasing": {"color": "red"}, "decreasing": {"color": "green"}},
                number={"suffix": "/100"},
                title={"text": f"Risk Level: {overall['risk_level']}"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": risk_color(overall["risk_level"])},
                    "steps": [
                        {"range": [0, 30], "color": "#1f8f3a"},
                        {"range": [30, 60], "color": "#d98c1f"},
                        {"range": [60, 100], "color": "#d62728"},
                    ],
                    "threshold": {"line": {"color": "white", "width": 4}, "thickness": 0.75, "value": overall["risk_score"]},
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)

            if overall["risk_level"] == "Low":
                st.balloons()

            # -------- DONUT CHART --------
            st.subheader("🔍 Safe vs Low-Value Mix")

            pie = pd.DataFrame({
                "Type": ["Safe", "Low-Value"],
                "Value": [overall["safe_share"], overall["low_value_share"]]
            })

            fig_pie = px.pie(
                pie,
                names="Type",
                values="Value",
                hole=0.55,
                color="Type",
                color_discrete_map={"Safe": "green", "Low-Value": "red"},
                title="Transaction Mix"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            st.caption(
                f"Low-Value Share = {overall['low_value_share']:.1f}% of selected transactions are below the dataset median benchmark "
                f"(₹{benchmark_median:.2f})."
            )

            # -------- DISTRIBUTION CHART --------
            st.subheader("📈 Transaction Value Spread")

            fig_hist = px.histogram(
                selected,
                x="TotalPrice",
                nbins=30,
                title="Selected Segment Transaction Distribution"
            )
            fig_hist.add_vline(
                x=benchmark_median,
                line_width=3,
                line_dash="dash",
                line_color="cyan"
            )
            fig_hist.add_vline(
                x=overall["avg_value"],
                line_width=3,
                line_dash="dot",
                line_color="yellow"
            )
            fig_hist.update_layout(
                xaxis_title="Transaction Value",
                yaxis_title="Count"
            )
            st.plotly_chart(fig_hist, use_container_width=True)

            st.info(
                f"Blue dashed line = dataset median benchmark ₹{benchmark_median:.2f}. "
                f"Yellow dotted line = selected segment average ₹{overall['avg_value']:.2f}. "
                f"This helps explain why the segment is classified as {overall['risk_level']} risk."
            )

            # -------- CATEGORY ANALYSIS --------
            st.subheader("📊 Category Risk Analysis")

            # Compare categories under the same selected context, but do not lock category itself.
            cat_context = apply_filters(
                df,
                gender_sel=gender,
                category_sel="All",
                payment_sel=payment,
                price_range=price,
                quantity_range=quantity,
                mall_sel=mall
            )

            cat_table = build_group_risk_table(cat_context, "category", benchmark_median)

            if cat_table.empty:
                st.warning("No category comparison available in the selected context.")
            else:
                fig_cat = px.bar(
                    cat_table,
                    x="category",
                    y="Risk Score",
                    color="Risk Level",
                    text=cat_table["Risk Score"].round(1),
                    color_discrete_map={"Low": "green", "Medium": "orange", "High": "red"},
                    title="Category Risk Score"
                )
                fig_cat.update_traces(textposition="outside")
                st.plotly_chart(fig_cat, use_container_width=True)

                top_cat = cat_table.sort_values("Risk Score", ascending=False).iloc[0]
                bottom_cat = cat_table.sort_values("Risk Score", ascending=True).iloc[0]

                st.info(
                    f"Category Insight: **{top_cat['category']}** is the riskiest category in this context "
                    f"with a score of **{top_cat['Risk Score']:.1f}**. "
                    f"The safest category here is **{bottom_cat['category']}** with a score of **{bottom_cat['Risk Score']:.1f}**. "
                    f"These values are computed from the transaction values inside the current filter context."
                )

                st.dataframe(
                    cat_table[["category", "Transactions", "Avg Value", "Low Value %", "Risk Score", "Risk Level"]],
                    use_container_width=True
                )

            # -------- GENDER ANALYSIS --------
            st.subheader("👥 Gender Risk Analysis")

            gen_context = apply_filters(
                df,
                gender_sel="All",
                category_sel=category,
                payment_sel=payment,
                price_range=price,
                quantity_range=quantity,
                mall_sel=mall
            )

            gen_table = build_group_risk_table(gen_context, "gender", benchmark_median)

            if gen_table.empty:
                st.warning("No gender comparison available in the selected context.")
            else:
                fig_gen = px.bar(
                    gen_table,
                    x="gender",
                    y="Risk Score",
                    color="Risk Level",
                    text=gen_table["Risk Score"].round(1),
                    color_discrete_map={"Low": "green", "Medium": "orange", "High": "red"},
                    title="Gender Risk Score"
                )
                fig_gen.update_traces(textposition="outside")
                st.plotly_chart(fig_gen, use_container_width=True)

                top_gen = gen_table.sort_values("Risk Score", ascending=False).iloc[0]
                bottom_gen = gen_table.sort_values("Risk Score", ascending=True).iloc[0]

                st.info(
                    f"Gender Insight: **{top_gen['gender']}** has the higher risk score in this context "
                    f"at **{top_gen['Risk Score']:.1f}**. "
                    f"**{bottom_gen['gender']}** is lower at **{bottom_gen['Risk Score']:.1f}**. "
                    f"Both are benchmarked against the same dataset median."
                )

                st.dataframe(
                    gen_table[["gender", "Transactions", "Avg Value", "Low Value %", "Risk Score", "Risk Level"]],
                    use_container_width=True
                )

            # -------- PAYMENT ANALYSIS --------
            st.subheader("💳 Payment Risk Analysis")

            pay_context = apply_filters(
                df,
                gender_sel=gender,
                category_sel=category,
                payment_sel="All",
                price_range=price,
                quantity_range=quantity,
                mall_sel=mall
            )

            pay_table = build_group_risk_table(pay_context, "payment_method", benchmark_median)

            if pay_table.empty:
                st.warning("No payment comparison available in the selected context.")
            else:
                fig_pay = px.bar(
                    pay_table,
                    x="payment_method",
                    y="Risk Score",
                    color="Risk Level",
                    text=pay_table["Risk Score"].round(1),
                    color_discrete_map={"Low": "green", "Medium": "orange", "High": "red"},
                    title="Payment Method Risk Score"
                )
                fig_pay.update_traces(textposition="outside")
                st.plotly_chart(fig_pay, use_container_width=True)

                top_pay = pay_table.sort_values("Risk Score", ascending=False).iloc[0]
                st.info(
                    f"Payment Insight: **{top_pay['payment_method']}** has the highest risk score "
                    f"of **{top_pay['Risk Score']:.1f}** in the current context. "
                    f"Use this to decide which payment mode needs stronger incentives or monitoring."
                )

                st.dataframe(
                    pay_table[["payment_method", "Transactions", "Avg Value", "Low Value %", "Risk Score", "Risk Level"]],
                    use_container_width=True
                )

            # -------- MALL ANALYSIS --------
            st.subheader("🏬 Shopping Mall Risk Analysis")

            mall_context = apply_filters(
                df,
                gender_sel=gender,
                category_sel=category,
                payment_sel=payment,
                price_range=price,
                quantity_range=quantity,
                mall_sel="All"
            )

            mall_table = build_group_risk_table(mall_context, "shopping_mall", benchmark_median)

            if mall_table.empty:
                st.warning("No mall comparison available in the selected context.")
            else:
                fig_mall = px.bar(
                    mall_table.head(8),
                    x="shopping_mall",
                    y="Risk Score",
                    color="Risk Level",
                    text=mall_table.head(8)["Risk Score"].round(1),
                    color_discrete_map={"Low": "green", "Medium": "orange", "High": "red"},
                    title="Mall Risk Score (Top 8)"
                )
                fig_mall.update_traces(textposition="outside")
                st.plotly_chart(fig_mall, use_container_width=True)

                top_mall = mall_table.sort_values("Risk Score", ascending=False).iloc[0]
                st.info(
                    f"Mall Insight: **{top_mall['shopping_mall']}** shows the highest risk score "
                    f"of **{top_mall['Risk Score']:.1f}** in the current context."
                )

            # -------- FINAL INSIGHT --------
            st.subheader("💡 Final Business Insight")

            st.write(
                f"""
- Overall Risk Score: **{overall['risk_score']:.1f}/100** ({overall['risk_level']})  
- Selected segment revenue: **₹{overall['revenue']:,.0f}**  
- Average transaction in this segment: **₹{overall['avg_value']:.2f}**  
- Transactions below benchmark median: **{overall['low_value_share']:.1f}%**  

👉 Interpretation:
- Lower low-value share means safer business behaviour.
- Higher risk score means the selected segment contains more low-value transactions compared to the dataset benchmark.
- The category/gender/payment/mall charts are compared within the current filter context, so the insights remain accurate.
"""
            )
