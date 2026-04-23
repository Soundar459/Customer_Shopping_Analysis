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

# ---------------- FILTER FUNCTION ----------------
def apply_filters(df, gender, category, payment, price, quantity):
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

# ---------------- RISK CALCULATION ----------------
def compute_risk(df, benchmark):
    if df.empty:
        return 0, 0, 0, 0

    avg = df["TotalPrice"].mean()
    low_share = (df["TotalPrice"] < benchmark).mean() * 100
    safe = 100 - low_share

    risk_score = (0.7 * low_share) + (0.3 * max(0, (benchmark - avg) / benchmark * 100))
    risk_score = np.clip(risk_score, 0, 100)

    return risk_score, low_share, safe, avg

def risk_level(score):
    if score < 30:
        return "Low"
    elif score < 60:
        return "Medium"
    return "High"

# ---------------- BENCHMARK ----------------
benchmark = df["TotalPrice"].median()

# ---------------- UI ----------------
st.subheader("🎯 Business Decision Engine")

col1, col2 = st.columns(2)

gender = col1.selectbox("Gender", ["All"] + list(df["gender"].unique()))
category = col1.selectbox("Category", ["All"] + list(df["category"].unique()))
payment = col2.selectbox("Payment Method", ["All"] + list(df["payment_method"].unique()))

price = col1.slider("Price Range", int(df.price.min()), int(df.price.max()),
                    (int(df.price.min()), int(df.price.max())))

quantity = col2.slider("Quantity Range", int(df.quantity.min()), int(df.quantity.max()),
                       (int(df.quantity.min()), int(df.quantity.max())))

# ---------------- ANALYZE ----------------
if st.button("🚀 Analyze"):

    filtered = apply_filters(df, gender, category, payment, price, quantity)

    if filtered.empty:
        st.error("No data for selected filters")
        st.stop()

    risk_score, low_share, safe_share, avg = compute_risk(filtered, benchmark)
    level = risk_level(risk_score)

    # ---------------- KPI ----------------
    st.subheader("📊 Overall Result")

    st.metric("Risk Score", f"{risk_score:.1f}/100")
    st.metric("Risk Level", level)
    st.metric("Avg Transaction", f"₹{avg:.2f}")

    # ---------------- GAUGE ----------------
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        title={'text': "Risk Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "red" if level=="High" else "orange" if level=="Medium" else "green"},
            'steps': [
                {'range': [0, 30], 'color': "green"},
                {'range': [30, 60], 'color': "orange"},
                {'range': [60, 100], 'color': "red"},
            ]
        }
    ))
    st.plotly_chart(fig_gauge, use_container_width=True)

    # ---------------- DONUT ----------------
    st.subheader("🔍 Safe vs Risk")

    pie = pd.DataFrame({
        "Type": ["Safe", "Risk"],
        "Value": [safe_share, low_share]
    })

    fig = px.pie(pie, names="Type", values="Value",
                 color="Type",
                 color_discrete_map={"Safe": "green", "Risk": "red"},
                 hole=0.5)

    st.plotly_chart(fig, use_container_width=True)

    st.info(f"{low_share:.1f}% transactions are low-value (below ₹{benchmark:.0f})")

    # ---------------- CATEGORY ANALYSIS ----------------
    st.subheader("📊 Category Analysis")

    cat_data = apply_filters(df, gender, "All", payment, price, quantity)

    rows = []

    for cat, grp in cat_data.groupby("category"):

        # ❌ REMOVE FAKE DATA
        if len(grp) < 5:
            continue

        r, l, s, a = compute_risk(grp, benchmark)

        rows.append({
            "Category": cat,
            "Risk Score": r,
            "Transactions": len(grp)
        })

    cat_df = pd.DataFrame(rows)

    if not cat_df.empty:

        fig = px.bar(cat_df,
                     x="Category",
                     y="Risk Score",
                     color="Risk Score",
                     color_continuous_scale=["green", "orange", "red"],
                     text=cat_df["Risk Score"].round(1))

        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

        high_cat = cat_df.loc[cat_df["Risk Score"].idxmax()]

        st.success(f"Highest Risk Category: {high_cat['Category']} ({high_cat['Risk Score']:.1f})")

    # ---------------- GENDER ANALYSIS ----------------
    st.subheader("👥 Gender Analysis")

    gen_data = apply_filters(df, "All", category, payment, price, quantity)

    rows = []

    for g, grp in gen_data.groupby("gender"):

        if len(grp) < 5:
            continue

        r, l, s, a = compute_risk(grp, benchmark)

        rows.append({
            "Gender": g,
            "Risk Score": r
        })

    gen_df = pd.DataFrame(rows)

    if not gen_df.empty:

        fig = px.bar(gen_df,
                     x="Gender",
                     y="Risk Score",
                     color="Risk Score",
                     color_continuous_scale=["green", "orange", "red"],
                     text=gen_df["Risk Score"].round(1))

        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    # ---------------- FINAL INSIGHT ----------------
    st.subheader("💡 Final Insight")

    st.write(f"""
- Risk Score: **{risk_score:.1f} ({level})**
- Average Value: **₹{avg:.2f}**
- Low-value transactions: **{low_share:.1f}%**

👉 Interpretation:
- High risk = more low-value purchases
- Low risk = strong customer spending
- All results are based ONLY on selected filters
""")
