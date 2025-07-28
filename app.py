import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import anthropic
import matplotlib.pyplot as plt
import joblib
import json
import os
from streamlit_plotly_events import plotly_events


# Load data
orders_df = pd.read_excel("myexc1.xlsx", sheet_name="Orders")
returns_df = pd.read_excel("myexc1.xlsx", sheet_name="Returns")
people_df = pd.read_excel("myexc1.xlsx", sheet_name="People")

# Set page and header style
st.set_page_config(layout="wide", page_title="Retail Intelligence Business Pulse Dashboard")

st.markdown("""
<style>
/* ====== GLOBAL THEME ====== */
html, body, .stApp {
    font-family: 'Segoe UI', sans-serif;
    background-color: #fffde7;  /* light yellow */
    color: #232F3E;
}

.block-container {
    padding: 1rem 2rem;
}

/* ====== HEADINGS ====== */
h1 {
    color: #FF9900;
    font-size: 2.2rem;
    font-weight: bold;
}

h2, h3 {
    color: #FF9900;
    font-weight: bold;
}

/* ====== SIDEBAR STYLING ====== */
[data-testid="stSidebar"] {
    background-color: #232F3E;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #FF9900 !important;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .css-16idsys {
    color: #FFFFFF !important;
    font-weight: 500;
}

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: white;
    color: black;
}

[data-testid="stSidebar"]::-webkit-scrollbar {
    width: 0.4em;
}
[data-testid="stSidebar"]::-webkit-scrollbar-thumb {
    background-color: #888;
    border-radius: 10px;
}

/* ====== BUTTONS ====== */
button {
    border-radius: 6px !important;
    font-weight: bold;
}
button[kind="primary"] {
    background-color: #FF9900 !important;
    color: black !important;
}

/* ====== KPI METRICS ====== */
[data-testid="stMetricLabel"] {
    color: #232F3E;
    font-size: 1rem;
}
[data-testid="stMetricValue"] {
    font-size: 1.6rem;
    font-weight: bold;
    color: #111;
}

/* ====== PLOTLY TITLES ====== */
.js-plotly-plot .gtitle {
    fill: #FF9900 !important;
    font-size: 18px;
    font-weight: bold;
}

/* ====== ST.TABS ====== */
div[data-baseweb="tab"] {
    font-size: 24px !important;
    font-weight: 700 !important;
    padding: 12px 24px !important;
    margin-right: 6px !important;
    border-radius: 10px 10px 0 0 !important;
    background-color: #f3f3f3 !important;
    color: #232F3E !important;
    border: 2px solid #ccc !important;
    border-bottom: none !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
    background-color: #FF9900 !important;
    color: black !important;
    font-weight: 800 !important;
    border-bottom: 3px solid #FF9900 !important;
}

/* ====== ST.RADIO (SUBTABS) ====== */
[data-testid="stRadio"] label {
    font-size: 18px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    margin-right: 0.5rem !important;
    border-radius: 8px !important;
    border: 1px solid #ccc !important;
    background-color: #f4f4f4 !important;
    transition: 0.3s ease;
}
[data-testid="stRadio"] label:hover {
    background-color: #ffe3b3 !important;
}
[data-testid="stRadio"] input:checked + div > label {
    background-color: #FF9900 !important;
    color: black !important;
    border-color: #FF9900 !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color:#FF9900;'>Retail Intelligence Business Pulse Dashboard</h1>", unsafe_allow_html=True)



tab_groups = {
    "OVERVIEW": ["Executive Overview", "EDA", "AI - Ask Data Anything"],
    "SALES PERFORMANCE ANALYSIS & PROFIT ANALYSIS": ["Sales Performance", "Profit Analysis", "Predict Profits"],
    "SHIPPING & RETURNS ANALYSIS": ["Shipping Analysis", "Return Analysis", "Returns Deep Dive", "Predict Return"],
    "GEO SPATIAL ANALYSIS": ["Geo Profit Map", "Region Manager View"],
    "SEGMENTATION ANALYSIS": ["Customer Segments", "Funnel Breakdown"]
}

main_tabs = st.tabs(list(tab_groups.keys()))

# Define tab names
#tab_names = ["Executive Overview", "Sales Performance", "Profit Analysis", "Shipping Analysis","Return Analysis", "Geo Profit Map", "Customer Segments", "Region Manager View","Funnel Breakdown", "Returns Deep Dive","AI - Ask Data Anything","EDA","Predict Return","Predict Profits"]
# Make sure session state key exists

#tabs = st.tabs([f"{i+1}. {name}" for i, name in enumerate(tab_names)])


# Global filters
with st.sidebar:
    st.markdown("## Global Filters")

    st.markdown("### Region")
    selected_region = st.multiselect(
        "Choose Regions",
        options=sorted(orders_df["Region"].dropna().unique()),
        default=sorted(orders_df["Region"].dropna().unique()),
        help="Filter by region",
    )

    st.markdown("### Segment")
    selected_segment = st.multiselect(
        "Choose Segments",
        options=sorted(orders_df["Segment"].dropna().unique()),
        default=sorted(orders_df["Segment"].dropna().unique()),
        help="Filter by segment"
    )

    st.markdown("### Category")
    selected_category = st.multiselect(
        "Choose Categories",
        options=sorted(orders_df["Category"].dropna().unique()),
        default=sorted(orders_df["Category"].dropna().unique()),
        help="Filter by product category"
    )

    st.markdown("---")
    st.markdown("### Order Date Range")

    min_date = pd.to_datetime(orders_df["Order Date"]).min()
    max_date = pd.to_datetime(orders_df["Order Date"]).max()

    date_filter_type = st.selectbox("Filter Type", ["Full Range", "2014", "2015", "2016", "2017", "Custom Range"])

    if date_filter_type == "Full Range":
        start_date, end_date = min_date, max_date
    elif date_filter_type in ["2014", "2015", "2016", "2017"]:
        year = int(date_filter_type)
        start_date = pd.to_datetime(f"{year}-01-01")
        end_date = pd.to_datetime(f"{year}-12-31")
    elif date_filter_type == "Custom Range":
        selected_date = st.date_input("Pick Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
        if isinstance(selected_date, (list, tuple)) and len(selected_date) == 2:
            start_date, end_date = pd.to_datetime(selected_date[0]), pd.to_datetime(selected_date[1])
        else:
            st.warning("Please select a valid custom date range.")
            start_date, end_date = min_date, max_date

# Apply filters
orders_df["Order Date"] = pd.to_datetime(orders_df["Order Date"])
orders_df["Ship Date"] = pd.to_datetime(orders_df["Ship Date"])
orders_filtered = orders_df[
    (orders_df["Region"].isin(selected_region)) &
    (orders_df["Segment"].isin(selected_segment)) &
    (orders_df["Category"].isin(selected_category)) &
    (orders_df["Order Date"] >= start_date) &
    (orders_df["Order Date"] <= end_date)
]

for i, (group_name, subtabs) in enumerate(tab_groups.items()):
    with main_tabs[i]:
        sub_tab = st.radio(f" {group_name} DRILL DOWN", subtabs, horizontal=True)
        
        # Tab 1: Executive Overview
        if sub_tab == "Executive Overview":
            st.markdown("""
            <style>
            .kpi-card {
                background-color: white;
                border-left: 5px solid #FF9900;
                padding: 1rem 1.2rem;
                margin: 0.6rem 0.8rem;
                border-radius: 10px;
                box-shadow: 1px 1px 8px rgba(0,0,0,0.05);
                min-width: 180px;
                text-align: left;
            }
            .kpi-title {
                color: #232F3E;
                font-size: 0.9rem;
                margin-bottom: 0.3rem;
                font-weight: 600;
            }
            .kpi-value {
                font-size: 1.6rem;
                font-weight: 700;
                color: black;
            }
            .kpi-delta {
                font-size: 0.85rem;
                font-weight: 500;
                margin-top: 0.2rem;
            }
            .kpi-green {
                color: green;
                background-color: #e0f6e9;
                border-radius: 8px;
                padding: 2px 6px;
            }
            .kpi-red {
                color: red;
                background-color: #fde4e4;
                border-radius: 8px;
                padding: 2px 6px;
            }
            </style>
            """, unsafe_allow_html=True)

            st.subheader("OverAll Summary Metrics")

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Sales", f"${orders_filtered['Sales'].sum():,.0f}")
            col2.metric("Total Profit", f"${orders_filtered['Profit'].sum():,.0f}")
            return_rate = orders_filtered['Return'].eq("Yes").mean() * 100
            col3.metric("Return Rate", f"{return_rate:.2f}%")
            delivery_lag = (orders_filtered["Ship Date"] - orders_filtered["Order Date"]).dt.days.mean()
            col4.metric("Avg Delivery Time", f"{delivery_lag:.1f} days")
            col5.metric("Orders", f"{orders_filtered['Order ID'].nunique()}")

            st.markdown("### Summary Metrics (YoY) - 2017 Vs 2016")

            # Ensure datetime parsing
            orders_df["Order Date"] = pd.to_datetime(orders_df["Order Date"])
            orders_df["Ship Date"] = pd.to_datetime(orders_df["Ship Date"])

            # Extract Year
            orders_df["Order Year"] = orders_df["Order Date"].dt.year

            # Define this year and last year from data
            latest_year = orders_df["Order Year"].max()
            prev_year = latest_year - 1

            # Subset
            df_curr = orders_df[orders_df["Order Year"] == latest_year]
            df_prev = orders_df[orders_df["Order Year"] == prev_year]

            # --- Compute Metrics ---
            def calc_delta(curr, prev):
                if prev == 0:
                    return "N/A"
                return f"{((curr - prev) / prev) * 100:.1f}%"

            # 1. Total Sales
            sales_curr = df_curr["Sales"].sum()
            sales_prev = df_prev["Sales"].sum()
            sales_delta = calc_delta(sales_curr, sales_prev)

            # 2. Total Profit
            profit_curr = df_curr["Profit"].sum()
            profit_prev = df_prev["Profit"].sum()
            profit_delta = calc_delta(profit_curr, profit_prev)

            # 3. Return Rate
            return_curr = df_curr["Return"].value_counts(normalize=True).get("Yes", 0)
            return_prev = df_prev["Return"].value_counts(normalize=True).get("Yes", 0)
            return_delta = calc_delta(return_curr, return_prev)

            # 4. Avg Order Value (AOV)
            aov_curr = sales_curr / df_curr["Order ID"].nunique()
            aov_prev = sales_prev / df_prev["Order ID"].nunique()
            aov_delta = calc_delta(aov_curr, aov_prev)

            # 5. Delivery Lag
            df_curr["Lag"] = (df_curr["Ship Date"] - df_curr["Order Date"]).dt.days
            df_prev["Lag"] = (df_prev["Ship Date"] - df_prev["Order Date"]).dt.days
            lag_curr = df_curr["Lag"].mean()
            lag_prev = df_prev["Lag"].mean()
            lag_delta = f"{lag_curr - lag_prev:.1f} days"

            # 6. Orders
            order_count_curr = df_curr["Order ID"].nunique()
            order_count_prev = df_prev["Order ID"].nunique()
            order_delta = calc_delta(order_count_curr, order_count_prev)

            # --- Display KPIs with Amazon-themed background boxes ---
            kpi_data = [
                {"label": "Total Sales", "value": f"${sales_curr:,.0f}", "delta": sales_delta, "delta_color": "green" if "-" not in sales_delta else "red"},
                {"label": "Total Profit", "value": f"${profit_curr:,.0f}", "delta": profit_delta, "delta_color": "green" if "-" not in profit_delta else "red"},
                {"label": "Return Rate", "value": f"{return_curr:.1%}", "delta": return_delta, "delta_color": "green" if "-" not in return_delta else "red"},
                {"label": "Avg Order Value", "value": f"${aov_curr:.0f}", "delta": aov_delta, "delta_color": "green" if "-" not in aov_delta else "red"},
                {"label": "Avg Delivery Time", "value": f"{lag_curr:.1f} days", "delta": lag_delta, "delta_color": "green" if "-" not in lag_delta else "red"},
                {"label": "Orders", "value": f"{order_count_curr:,}", "delta": order_delta, "delta_color": "green" if "-" not in order_delta else "red"},
            ]

            cols1 = st.columns(3)
            cols2 = st.columns(3)

            for i, metric in enumerate(kpi_data):
                col = cols1[i] if i < 3 else cols2[i - 3]
                with col:
                    st.markdown(
                        f"""
                        <div style='background-color:#FFF5D9;padding:20px 20px 15px;border-radius:10px;margin-bottom:10px'>
                            <div style='font-weight:bold;font-size:16px;color:#333;'>{metric['label']}</div>
                            <div style='font-size:24px;font-weight:700;color:#111;margin-top:5px'>{metric['value']}</div>
                            <div style='font-size:14px;color:{"#11A611" if metric["delta_color"] == "green" else "#CC0000"};margin-top:5px'>
                                {metric['delta']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )



            col1, col2, col3 = st.columns(3)
            st.markdown("""
                <style>
                .insight-block {
                    background-color: #ffffff;
                    border: 2px solid #FF9900;
                    padding: 1.2rem 1.5rem;
                    margin-bottom: 1.2rem;
                    border-radius: 12px;
                    box-shadow: 2px 2px 10px rgba(255, 153, 0, 0.1);
                }
                .insight-block h4 {
                    color: #FF9900;
                    font-size: 1.15rem;
                    margin-bottom: 0.5rem;
                    font-weight: 700;
                }
                .insight-block ul {
                    padding-left: 1.3rem;
                    margin-bottom: 0.2rem;
                }
                .insight-block li {
                    margin-bottom: 0.4rem;
                    line-height: 1.5;
                    font-size: 0.95rem;
                    color: #232F3E;
                }
                </style>
                """, unsafe_allow_html=True)

        

            with col1:
                st.markdown("### Executive Summary & Insights")

                st.markdown("""
                <div class='insight-block'>
                    <h4>Executive Overview</h4>
                    <ul>
                        <li> Total Sales and Profit show seasonal trends with peak months. Every year mainly around Mar,Sep,Nov and Dec we see a spike in Sales(Aliging to holidays - Big Spring Sale, Labor Day, Thanksgiving & Christmas).Other months seems very stable and constant.</li>
                    </ul>
                </div>

                <div class='insight-block'>
                    <h4>Sales & Profit Performance</h4>
                    <ul>
                        <li>Technology leads in sales, but Office Supplies shows consistent YoY growth.Segment-wise, Corporate has highest sales, but Consumer is growing fastest.High-profit margins in Technology, especially Phones and Accessories.Tables (Furniture) consistently show losses , consider re-pricing or phasing out.</li>
                    </ul>
                </div>

                <div class='insight-block'>
                    <h4>Shipping Analysis</h4>
                    <ul>
                        <li> Most orders are shipped via Standard Class.Very low return-to-order ratio (~8%), which is within acceptable range.First Class has lower lag but is underused; optimize usage for high-margin orders.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("### Executive Summary & Insights (Contd.)")

                st.markdown("""
                <div class='insight-block'>
                    <h4>Return Analysis</h4>
                    <ul>
                        <li> Phones and Binders are among the most returned products.Discounted items have marginally higher return rates , monitor closely.Higher discounts correlate slightly with higher returns.Seasonal spikes in returns around Q4 , suggests post-holiday product dissatisfaction.</li>
                    </ul>
                </div>

                <div class='insight-block'>
                    <h4>Spatial & Customer Segmentation</h4>
                    <ul>
                        <li>California, New York lead in profit, where as Texas looks like a problemetic state wrt profitability.Several Midwest states have low or negative profit , targeted marketing may help.Small cluster of high-AOV, high-frequency customers drive major profit.Consider loyalty program or tailored upsells.</li>
                    </ul>
                </div>

                <div class='insight-block'>
                    <h4>Region Manager View</h4>
                    <ul>
                        <li> West and East outperform Central in sales.Sub-categories like Tables and Machines cause operational inefficiencies (slow delivery, high returns).</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown("### Strategic Recommendations")

                st.markdown("""
                <div class='insight-block'>
                    <h4>Operational Tuning</h4>
                    <ul>
                        <li> Recalibrate shipping tiers : offer faster options for high-margin orders.Phase out or re-price Tables : a loss driver across all segments.</li>
                        <li> Top 10 customers contribute disproportionately to profit : offer loyalty programs.Correlation observed between Discount > 20 percent and Return Rate > 10 percent: tighten markdown policies.</li>
                    </ul>
                </div>
                            
                <div class='insight-block'>
                    <h4>Geographic Strategy</h4>
                    <ul>
                            <li>Underperformance in Midwest and South : explore targeted promotions.</li>
                            <li>Focus retention campaigns in NY, CA where LTV is highest.</li>
                    </ul>
                </div>

                <div class='insight-block'>
                    <h4>Customer Targeting</h4>
                    <ul>
                        <li> **Binders and Phones** are return-heavy : investigate product quality or mismatch.</li>
                        <li> **Corporate + Technology** segment is ideal for upsell and bundling.</li></ul>
                </div>
                            
                """, unsafe_allow_html=True)


                
        elif sub_tab == "Sales Performance":
                    st.markdown("### Monthly Sales Trend")
                    monthly_df = orders_filtered.copy()
                    monthly_df["Month"] = monthly_df["Order Date"].dt.to_period("M").astype(str)
                    monthly_sales = monthly_df.groupby("Month")["Sales"].sum().reset_index()

                    fig1 = px.line(monthly_sales, x="Month", y="Sales", markers=True,
                                title="Monthly Sales Trend", labels={"Sales": "Sales ($)"})
                    fig1.update_layout(margin=dict(t=40, l=20, r=20, b=20), height=400)

                    st.plotly_chart(fig1, use_container_width=True)

                    # Split layout below
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("### Sales by Segment")
                        segment_sales = orders_filtered.groupby("Segment")["Sales"].sum().reset_index().sort_values(by="Sales", ascending=False)
                        fig2 = px.bar(segment_sales, x="Segment", y="Sales", color="Segment",
                                    title="Sales by Segment", text_auto=".2s", labels={"Sales": "Sales ($)"})
                        fig2.update_layout(margin=dict(t=40, l=10, r=10, b=20), height=800)
                        st.plotly_chart(fig2, use_container_width=True)

                    with col2:
                        st.markdown("### Sales by Category and Sub-Category")
                        cat_sub = orders_filtered.groupby(["Category", "Sub-Category"])["Sales"].sum().reset_index()
                        fig3 = px.bar(cat_sub, x="Sales", y="Sub-Category", color="Category",
                                    orientation="h", title="Category → Sub-Category Drilldown", text_auto=".2s",
                                    labels={"Sales": "Sales ($)"})
                        fig3.update_layout(margin=dict(t=40, l=10, r=10, b=20), height=800)
                        st.plotly_chart(fig3, use_container_width=True)
        elif sub_tab == "Profit Analysis":
                st.subheader("Profit Analysis")

                # KPIs
                total_profit = orders_filtered["Profit"].sum()
                profit_margin = (total_profit / orders_filtered["Sales"].sum()) * 100 if orders_filtered["Sales"].sum() != 0 else 0
                least_prof_cat = orders_filtered.groupby("Category")["Profit"].sum().idxmin()

                col1, col2, col3 = st.columns(3)
                col1.metric("Total Profit", f"${total_profit:,.0f}")
                col2.metric("Profit Margin %", f"{profit_margin:.2f}%")
                col3.metric("Lowest Profit Category", least_prof_cat)

                # Profit by Category/Sub-Category Bar Chart
                st.markdown("### Profit by Category → Sub-Category -> ProductName")
                profit_df = orders_filtered.groupby(["Category", "Sub-Category"])["Profit"].sum().reset_index()
                fig = px.bar(
                    profit_df,
                    x="Profit",
                    y="Sub-Category",
                    color="Category",
                    orientation="h",
                    title="Profit Breakdown By Category & Sub-Category View",
                    text_auto=".2s"
                )
                fig.update_layout(height=800, margin=dict(t=40, l=10, r=10, b=20))
                st.plotly_chart(fig, use_container_width=True)

                # Step 0: Session drill state
                drill_category = st.session_state.get("selected_category")
                drill_subcat = st.session_state.get("selected_subcat")

                # CATEGORY LEVEL VIEW
                if not drill_category:
                    st.markdown("### Profit by Category")

                    df_cat = orders_filtered.groupby("Category", as_index=False)["Profit"].sum()
                    
                    df_cat["Profit"] = df_cat["Profit"].astype(float)
                    
                    df_cat["Color"] = df_cat["Profit"].apply(lambda x: "green" if x >= 0 else "crimson")

                    fig = go.Figure(data=[
                        go.Bar(
                            x=df_cat["Category"],
                            y=df_cat["Profit"].tolist(),
                            marker_color=df_cat["Color"],
                            text=df_cat["Profit"].apply(lambda x: f"${x:,.0f}"),
                            textposition="outside"
                        )
                    ])

                    fig.update_layout(
                        title="Click a Category to drill into Sub-Categories",
                        xaxis_title="Category",
                        yaxis_title="Total Profit ($)")

                    click = plotly_events(fig, click_event=True, override_height=800)

                    if click:
                        st.session_state["selected_category"] = click[0]["x"]
                        st.rerun()

                # SUB-CATEGORY LEVEL VIEW
                elif drill_category and not drill_subcat:
                    st.markdown(f"### 🔍 Sub-Category Profit for **{drill_category}**")

                    df_subcat = orders_filtered[orders_filtered["Category"] == drill_category]
                    df_subcat = df_subcat.groupby("Sub-Category", as_index=False)["Profit"].sum()
                    df_subcat["Color"] = df_subcat["Profit"].apply(lambda x: "green" if x >= 0 else "crimson")


                    fig_sub = go.Figure(data=[
                        go.Bar(
                            x=df_subcat["Sub-Category"],
                            y=df_subcat["Profit"].tolist(),
                            marker_color=df_subcat["Color"],
                            text=df_subcat["Profit"].apply(lambda x: f"${x:,.0f}"),
                            textposition="outside"
                        )
                    ])

                    # Update layout (no y-axis ticks)
                    fig_sub.update_layout(
                        title="Click a Sub-Category to drill into Products",
                        xaxis_title="Sub-Category",
                        yaxis_title="Total Profit ($)",
                        height=800
                    )

                    # Correct usage of plotly_events
                    click = plotly_events(fig_sub, click_event=True, override_height=800)
                    
                    col1, col2 = st.columns([1, 3])
                    if col1.button("🔙 Back"):
                        del st.session_state["selected_category"]
                        st.rerun()

                    if click:
                        st.session_state["selected_subcat"] = click[0]["x"]
                        st.rerun()

                # PRODUCT LEVEL VIEW
                elif drill_category and drill_subcat:
                    st.markdown(f"### Product Profit for **{drill_subcat}** under **{drill_category}**")

                    df_product = orders_filtered[
                        (orders_filtered["Category"] == drill_category) &
                        (orders_filtered["Sub-Category"] == drill_subcat)
                    ]
                    df_product = df_product.groupby("Product Name", as_index=False)["Profit"].sum()
                    df_product["Color"] = df_product["Profit"].apply(lambda x: "green" if x >= 0 else "crimson")

                    fig_prod = px.bar(df_product, x="Product Name", y="Profit", color="Color",
                                    color_discrete_map="identity", title="Product-level Profit")
                    fig_prod.update_layout(xaxis_tickangle=-45,height=800)

                    st.plotly_chart(fig_prod, use_container_width=True)

                    col1, col2 = st.columns([1, 3])
                    if col1.button("🔙 Back to Sub-Categories"):
                        del st.session_state["selected_subcat"]
                        st.rerun()

        elif sub_tab == 'Shipping Analysis':
                st.subheader("Shipping Analysis")
                # --- KPIs ---
                delivery_lags = (orders_filtered["Ship Date"] - orders_filtered["Order Date"]).dt.days
                avg_lag = delivery_lags.mean()
                late_pct = (delivery_lags > 5).mean() * 100  # Arbitrary 5-day cutoff for 'late'
                fastest_mode = orders_filtered.groupby("Ship Mode")["Ship Date"].apply(lambda x: (x - orders_filtered["Order Date"]).dt.days.mean()).idxmin()

                col1, col2, col3 = st.columns(3)
                col1.metric("Avg Shipping Delay", f"{avg_lag:.1f} days")
                col2.metric("% Orders Late (>5d)", f"{late_pct:.1f}%")
                col3.metric("Fastest Ship Mode", fastest_mode)

                # Split layout below
                col1, col2 = st.columns(2)

                with col1:
                    # --- Boxplot: Lag by Ship Mode ---
                    st.markdown("### Delivery Lag by Ship Mode")
                    lag_df = orders_filtered.copy()
                    lag_df["Lag (Days)"] = (lag_df["Ship Date"] - lag_df["Order Date"]).dt.days
                    fig1 = px.box(lag_df, x="Ship Mode", y="Lag (Days)", color="Ship Mode", points="outliers",
                                title="Delivery Lag by Shipping Mode")
                    fig1.update_layout(
                        height=600,
                        margin=dict(t=40, l=10, r=10, b=20),
                        font=dict(size=16),
                        title_font=dict(size=20)
                    )
                    st.plotly_chart(fig1, use_container_width=True)

                with col2:
                    # --- Stacked Bar: Ship Mode by Category ---
                    st.markdown("### Ship Mode Distribution by Category")
                    mode_dist = orders_filtered.groupby(["Category", "Ship Mode"]).size().reset_index(name="Count")
                    fig2 = px.bar(mode_dist, x="Category", y="Count", color="Ship Mode", barmode="stack",
                                title="Shipping Methods by Category")
                    fig2.update_layout(
                        height=600,
                        margin=dict(t=40, l=10, r=10, b=20),
                        font=dict(size=16),
                        title_font=dict(size=20)
                    )
                    st.plotly_chart(fig2, use_container_width=True)


                # --- State management for drilldown ---
                drill_category = st.session_state.get("ship_drill_category")

                # --- LEVEL 1: Category-Level Ship Mode Distribution ---
                if not drill_category:
                    st.subheader("Ship Mode Distribution by Category : Dive Deep")

                    ship_counts = orders_filtered.groupby(["Category", "Ship Mode"]).size().reset_index(name="Count")
                   
                    # Ship mode colors
                    ship_mode_colors = {
                        "Standard Class": "#1f77b4",  # dark blue
                        "Second Class": "#aec7e8",    # light blue
                        "First Class": "#ff9896",     # pinkish red
                        "Same Day": "#ffbb78",        # peach
                    }

                    # Create one Bar trace per Ship Mode
                    fig = go.Figure()

                    for ship_mode in ship_counts["Ship Mode"].unique():
                        filtered = ship_counts[ship_counts["Ship Mode"] == ship_mode]
                        fig.add_trace(go.Bar(
                            x=filtered["Category"],
                            y=filtered["Count"].tolist(),
                            name=ship_mode,
                            marker_color=ship_mode_colors.get(ship_mode, "#888"),
                        ))

                    # Layout: grouped bars (not stacked)
                    fig.update_layout(
                        barmode="group",
                        title="Ship Mode Distribution by Category",
                        xaxis_title="Category",
                        yaxis_title="Number of Shipments",
                        height=800,width=2000)

                    # Correct usage of plotly_events
                    click = plotly_events(fig, click_event=True, override_height=800)
                    
                    if click:
                        selected_category = click[0]["x"]
                        st.session_state["ship_drill_category"] = selected_category
                        st.rerun()

                # --- LEVEL 2: Sub-Category Drilldown ---
                else:
                    st.subheader(f"Sub-Category View for **{drill_category}**")
                    # --- Prepare shipping lag summary for drilldown ---
                    orders_filtered["Shipping Lag (Days)"] = (
                        orders_filtered["Ship Date"] - orders_filtered["Order Date"]
                    ).dt.days

                    shipping_lag_summary = orders_filtered.groupby(
                        ["Category", "Sub-Category", "Ship Mode"]
                    ).agg({
                        "Shipping Lag (Days)": "mean",
                        "Profit": "sum",
                        "Sales": "sum"
                    }).reset_index()

                    drill_df = shipping_lag_summary[shipping_lag_summary["Category"] == drill_category]

                    fig2 = px.bar(
                        drill_df,
                        x="Sub-Category",
                        y="Shipping Lag (Days)",
                        color="Ship Mode",
                        barmode="group",
                        hover_data=["Profit", "Sales"],
                        title=f"Avg Shipping Lag by Sub-Category and Ship Mode — {drill_category}",
                        height=500
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                    if st.button("🔙 Back to Category View"):
                        del st.session_state["ship_drill_category"]
                        st.rerun()


            
        elif sub_tab == "Return Analysis":
                st.subheader("Return Analysis")

                # --- Return Rate Calculations ---
                orders_filtered["Is Returned"] = orders_filtered["Return"].eq("Yes")
                return_rate = orders_filtered["Is Returned"].mean() * 100
                return_volume = orders_filtered["Is Returned"].sum()
                high_return_cat = orders_filtered.groupby("Category")["Is Returned"].mean().idxmax()

                col1, col2, col3 = st.columns(3)
                col1.metric("Return Rate", f"{return_rate:.2f}%")
                col2.metric("Return Volume", f"{return_volume}")
                col3.metric("Top Return Category", high_return_cat)

                # --- Bar Chart: Return Rate by Category/Sub-Category ---
                st.markdown("### Return Rate by Sub-Category")
                subcat_returns = orders_filtered.groupby(["Category", "Sub-Category"])["Is Returned"].mean().reset_index()
                fig1 = px.bar(
                    subcat_returns,
                    x="Is Returned", y="Sub-Category", color="Category", orientation="h",
                    title="Return Rate by Sub-Category",
                    labels={"Is Returned": "Return Rate"}
                )
                fig1.update_layout(
                    height=600,
                    margin=dict(t=40, l=10, r=10, b=20),
                    font=dict(size=16),
                    title_font=dict(size=20)
                )
                st.plotly_chart(fig1, use_container_width=True)

                # --- Heatmap: Sub-Category by Region ---
                st.markdown("### Return Rate Heatmap by Sub-Category & Region")
                heatmap_df = orders_filtered.groupby(["Region", "Sub-Category"])["Is Returned"].mean().reset_index()
                pivot = heatmap_df.pivot(index="Sub-Category", columns="Region", values="Is Returned").fillna(0)

                fig2 = px.imshow(
                    pivot,
                    text_auto=".1%",
                    color_continuous_scale="Reds",
                    aspect="auto",
                    labels=dict(color="Return %"),
                    title="Return Rate Heatmap"
                )
                fig2.update_layout(
                    height=600,
                    font=dict(size=14),
                    title_font=dict(size=20),
                    margin=dict(t=50, l=10, r=10, b=10)
                )
                st.plotly_chart(fig2, use_container_width=True)

        elif sub_tab == "Geo Profit Map":
                st.subheader("Geo Profit Map")

                # --- Map Chart: Profit by State ---
                state_profit = orders_filtered.groupby("State")["Profit"].sum().reset_index()
                
                # Mapping full state names to abbreviations
                us_state_abbrev = {
                    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
                    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
                    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
                    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
                    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
                    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
                    'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
                    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
                    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
                    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI',
                    'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX',
                    'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
                    'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
                }

                # Apply abbreviation mapping
                state_profit["State Abbrev"] = state_profit["State"].map(us_state_abbrev)

                fig1 = px.choropleth(
                    state_profit,
                    locations="State Abbrev",  # ← use abbrev
                    locationmode="USA-states",
                    color="Profit",
                    scope="usa",
                    color_continuous_scale="RdYlGn",
                    title="Profit by U.S. State"
                )

                fig1.update_layout(
                    height=700,
                    margin=dict(t=50, l=10, r=10, b=20),
                    font=dict(size=16),
                    title_font=dict(size=20)
                )
                st.plotly_chart(fig1, use_container_width=True)

                # --- Top 5 / Bottom 5 Profit States ---
                st.markdown("### Top & Bottom States by Profit")
                state_profit_sorted = state_profit.sort_values(by="Profit", ascending=False)
                top_states = state_profit_sorted.head(5)
                bottom_states = state_profit_sorted.tail(5)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### Top 5 States")
                    st.dataframe(top_states.style.format({"Profit": "${:,.0f}"}))

                with col2:
                    st.markdown("#### Bottom 5 States")
                    st.dataframe(bottom_states.style.format({"Profit": "${:,.0f}"}))

        elif sub_tab == "Customer Segments":
                st.subheader("Customer Segments")

                 # --- AOV and Orders ---
                cust_df = orders_filtered.groupby("Customer Name").agg({
                    "Order ID": pd.Series.nunique,
                    "Sales": "sum",
                    "Profit": "sum"
                }).reset_index().rename(columns={"Order ID": "Order Count"})
                cust_df["AOV"] = cust_df["Sales"] / cust_df["Order Count"]

                avg_aov = cust_df["AOV"].mean()
                avg_orders = cust_df["Order Count"].mean()
                top_segment = orders_filtered.groupby("Segment")["Profit"].sum().idxmax()

                col1, col2, col3 = st.columns(3)
                col1.metric("Avg AOV", f"${avg_aov:.2f}")
                col2.metric("Avg Orders/Customer", f"{avg_orders:.1f}")
                col3.metric("Top Profit Segment", top_segment)


                st.markdown("### AOV vs. Order Count per Customer - Customer Segmentation")

                # Step 1: Compute customer metrics
                cust_df = (
                    orders_filtered.groupby("Customer ID")
                    .agg({
                        "Order ID": pd.Series.nunique,
                        "Sales": "sum",
                        "Profit": "sum",
                        "Customer Name": "first"
                    })
                    .reset_index()
                    .rename(columns={"Order ID": "Order Count"})
                )

                cust_df["AOV"] = cust_df["Sales"] / cust_df["Order Count"]

                # Step 2: Compute averages
                avg_orders = cust_df["Order Count"].mean()
                avg_aov = cust_df["AOV"].mean()

                # Step 3: Classify customer segments
                cust_df["Order Segment"] = cust_df["Order Count"].apply(lambda x: "High Orders" if x > avg_orders else "Low Orders")
                cust_df["AOV Segment"] = cust_df["AOV"].apply(lambda x: "High AOV" if x > avg_aov else "Low AOV")
                cust_df["Segment"] = cust_df["Order Segment"] + " / " + cust_df["AOV Segment"]

                # Step 4: Color mapping
                color_map = {
                    "High Orders / High AOV": "#2ca02c",
                    "High Orders / Low AOV": "#1f77b4",
                    "Low Orders / High AOV": "#ff7f0e",
                    "Low Orders / Low AOV": "#d62728"
                }

                # Step 5: Plot
                fig = px.scatter(
                    cust_df,
                    x="Order Count",
                    y="AOV",
                    color="Segment",
                    color_discrete_map=color_map,
                    hover_data=["Customer Name", "Sales", "Profit"],
                    title="Customer Segmentation: Orders vs. AOV",
                )

                # Reference lines
                fig.add_vline(x=avg_orders, line_dash="dash", line_color="gray", annotation_text="Avg Orders", annotation_position="top left")
                fig.add_hline(y=avg_aov, line_dash="dash", line_color="gray", annotation_text="Avg AOV", annotation_position="bottom right")

                fig.update_layout(height=600)

                st.plotly_chart(fig, use_container_width=True)

                # --- Top 10 Customers by Profit ---
                st.markdown("### Top 10 Customers by Profit")
                top10 = cust_df.sort_values("Profit", ascending=False).head(10)[["Customer Name", "Profit", "Sales", "Order Count", "AOV"]]
                st.dataframe(top10.style.format({"Profit": "${:,.0f}", "Sales": "${:,.0f}", "AOV": "${:,.2f}"}))
        
        elif sub_tab == "Region Manager View":
                st.markdown("<h2 style='color:#ff9900;'>Region Manager View: Detailed Comparison</h2>", unsafe_allow_html=True)

                all_regions = sorted(orders_filtered["Region"].dropna().unique())
                selected_region = st.selectbox("Select Region (This)", all_regions, key="region_this")
                
                if len(selected_region) > 0:
                    manager_row = people_df[people_df["Region"] == selected_region]
                    if not manager_row.empty:
                        manager_name = manager_row.iloc[0]["Person"]
                        st.markdown(f"#### ***Region Manager for **{selected_region}**: `{manager_name}`")
                    else:
                        st.markdown(f"#### No manager assigned for region **{selected_region}**.")
                else:
                    st.markdown("#### Please select a single region to view the manager name.")

                
                compare_to = st.selectbox("Compare Against (That)", ["All Other Regions"] + [r for r in all_regions if r != selected_region], key="region_that")

                if len(compare_to) > 0:
                    manager_row_that = people_df[people_df["Region"] == compare_to]
                    if not manager_row_that.empty:
                        manager_name_that = manager_row_that.iloc[0]["Person"]
                        st.markdown(f"#### ***Region Manager for **{compare_to}**: `{manager_name_that}`")
                    else:
                        st.markdown(f"#### No manager assigned for region **{compare_to}**.")
                else:
                    st.markdown("#### Please select a single region to view the manager name.")


                df_this = orders_filtered[orders_filtered["Region"] == selected_region]
                if compare_to == "All Other Regions":
                    df_that = orders_filtered[orders_filtered["Region"] != selected_region]
                else:
                    df_that = orders_filtered[orders_filtered["Region"] == compare_to]

                                # Company-wide totals
                company_sales = orders_filtered["Sales"].sum()
                company_profit = orders_filtered["Profit"].sum()
                company_returns = orders_filtered["Return"].eq("Yes").sum()

                # Function to compute KPIs
                def get_metrics(df):
                    return {
                        "Sales": df["Sales"].sum(),
                        "Profit": df["Profit"].sum(),
                        "Return Rate (%)": df["Return"].eq("Yes").mean() * 100,
                        "Avg Delivery (days)": (pd.to_datetime(df["Ship Date"]) - pd.to_datetime(df["Order Date"])).dt.days.mean()
                    }

                this_metrics = get_metrics(df_this)
                that_metrics = get_metrics(df_that)

                # % Contribution
                contribution = {
                    "Sales": 100 * this_metrics["Sales"] / company_sales,
                    "Profit": 100 * this_metrics["Profit"] / company_profit,
                    "Returns": 100 * df_this["Return"].eq("Yes").sum() / company_returns
                }

                st.markdown("### Contribution to Total Company Metrics")
                c1, c2, c3 = st.columns(3)
                c1.metric("Sales Contribution (%)", f"{contribution['Sales']:.2f}%")
                c2.metric("Profit Contribution (%)", f"{contribution['Profit']:.2f}%")
                c3.metric("Return Volume Contribution (%)", f"{contribution['Returns']:.2f}%")

                # KPI side-by-side
                st.markdown(f"### KPI Comparison: {selected_region} vs. {compare_to}")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"#### 🟡 {selected_region}")
                    for k, v in this_metrics.items():
                        st.metric(k, f"{v:,.2f}")
                with col2:
                    st.markdown(f"#### ⚫ {compare_to}")
                    for k, v in that_metrics.items():
                        st.metric(k, f"{v:,.2f}")

                # --- Region Rank Charts ---
                st.markdown("### Region Leaderboards")

                rank_df = orders_filtered.groupby("Region").agg({
                    "Sales": "sum",
                    "Profit": "sum",
                    "Return": lambda x: x.eq("Yes").mean() * 100
                }).reset_index().rename(columns={"Return": "Return Rate (%)"})

                colr1, colr2, colr3 = st.columns(3)
                with colr1:
                    fig1 = px.bar(rank_df.sort_values("Sales", ascending=False),
                                x="Sales", y="Region", orientation="h", title="Sales by Region")
                    st.plotly_chart(fig1, use_container_width=True)
                with colr2:
                    fig2 = px.bar(rank_df.sort_values("Profit", ascending=False),
                                x="Profit", y="Region", orientation="h", title="Profit by Region")
                    st.plotly_chart(fig2, use_container_width=True)
                with colr3:
                    fig3 = px.bar(rank_df.sort_values("Return Rate (%)", ascending=False),
                                x="Return Rate (%)", y="Region", orientation="h", title="Return Rate by Region")
                    st.plotly_chart(fig3, use_container_width=True)

                # --- Trends: Sales & Profit Over Time ---
                st.markdown("### Monthly Trend Comparison")
                orders_filtered["Order Month"] = pd.to_datetime(orders_filtered["Order Date"]).dt.to_period("M").astype(str)
                trend_df = orders_filtered[orders_filtered["Region"].isin([selected_region] + ([] if compare_to == "All Other Regions" else [compare_to]))]
                trend_group = trend_df.groupby(["Order Month", "Region"]).agg({
                    "Sales": "sum",
                    "Profit": "sum"
                }).reset_index()

                colt1, colt2 = st.columns(2)
                with colt1:
                    fig4 = px.line(trend_group, x="Order Month", y="Sales", color="Region", title="Monthly Sales")
                    fig4.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig4, use_container_width=True)
                with colt2:
                    fig5 = px.line(trend_group, x="Order Month", y="Profit", color="Region", title="Monthly Profit")
                    fig5.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig5, use_container_width=True)
                
                # --- Return Rate Heatmap by Sub-Category & Region ---
                st.markdown("### Return Rate Heatmap by Sub-Category & Region")

                heatmap_df = orders_filtered.groupby(["Sub-Category", "Region"])["Return"].apply(lambda x: x.eq("Yes").mean() * 100).reset_index()
                heatmap_pivot = heatmap_df.pivot(index="Sub-Category", columns="Region", values="Return")

                fig_heatmap = px.imshow(
                    heatmap_pivot,
                    text_auto=".1f",
                    color_continuous_scale="Reds",
                    aspect="auto",
                    title="Return Rate (%)"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)


                # --- Delivery Lag vs Profit Bubble Chart (by Sub-Category) ---
                st.markdown("### Avg Delivery Lag vs Total Profit (by Sub-Category)")

                bubble_df = orders_filtered.copy()
                bubble_df["Delivery Lag"] = (bubble_df["Ship Date"] - bubble_df["Order Date"]).dt.days
                bubble_summary = bubble_df.groupby("Sub-Category").agg({
                    "Profit": "sum",
                    "Delivery Lag": "mean",
                    "Sales": "sum"
                }).reset_index()

                fig_bubble = px.scatter(
                    bubble_summary,
                    x="Delivery Lag", y="Profit",
                    size="Sales", color="Sub-Category",
                    text="Sub-Category",
                    title="Avg Delivery Lag vs Total Profit (by Sub-Category)",
                    size_max=40
                )
                fig_bubble.update_traces(textposition="top center")
                st.plotly_chart(fig_bubble, use_container_width=True)

         
        elif sub_tab == "Funnel Breakdown":
                st.subheader("Funnel Breakdown: Order → Ship → Return")

                # Create stages manually
                total_orders = orders_filtered["Order ID"].nunique()
                total_returns = orders_filtered[orders_filtered["Return"] == "Yes"]["Order ID"].nunique()
                total_shipped = total_orders  # Assuming all orders were shipped

                funnel_df = pd.DataFrame({
                    "Stage": ["Ordered", "Shipped", "Returned"],
                    "Count": [total_orders, total_shipped, total_returns]
                })

                conv_rate = (total_shipped / total_orders) * 100 if total_orders else 0
                return_rate = (total_returns / total_shipped) * 100 if total_shipped else 0
                drop_rate = 100 - return_rate

                # --- KPIs ---
                col1, col2, col3 = st.columns(3)
                col1.metric("Orders", f"{total_orders}")
                col2.metric("Shipped", f"{total_shipped} ({conv_rate:.1f}%)")
                col3.metric("Returned", f"{total_returns} ({return_rate:.1f}%)")

                # --- Funnel-style Bar Chart ---
                st.markdown("### Funnel Stages")
                fig1 = px.bar(
                    funnel_df, x="Stage", y="Count", color="Stage",
                    text="Count", title="Customer Order → Return Funnel"
                )
                fig1.update_layout(
                    height=400,
                    font=dict(size=16),
                    title_font=dict(size=20),
                    margin=dict(t=50, l=10, r=10, b=20)
                )
                st.plotly_chart(fig1, use_container_width=True, key="funnel_bar")

                # --- Optional Sankey Chart (Order → Ship → Return) ---
                st.markdown("### Sankey View (Flow from Order → Return)")

                label = ["Ordered", "Shipped", "Returned"]
                source = [0, 1]  # Ordered → Shipped → Returned
                target = [1, 2]
                value = [total_shipped, total_returns]

                fig2 = go.Figure(data=[go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=label,
                        color=["#1f77b4", "#2ca02c", "#d62728"]
                    ),
                    link=dict(
                        source=source,
                        target=target,
                        value=value
                    ))])

                fig2.update_layout(
                    title_text="Order → Ship → Return Flow",
                    font_size=16,
                    height=500
                )
                st.plotly_chart(fig2, use_container_width=True, key="funnel_sankey")

        elif sub_tab == "Returns Deep Dive":
                st.subheader("Returns Deep Dive")

                # --- KPI calculations ---
                orders_filtered["Is Returned"] = orders_filtered["Return"] == "Yes"
                avg_return_pct = orders_filtered["Is Returned"].mean() * 100
                avg_discount = orders_filtered["Discount"].mean()
                high_return_subcat = orders_filtered.groupby("Sub-Category")["Is Returned"].mean().idxmax()

                col1, col2, col3 = st.columns(3)
                col1.metric("Avg Return Rate", f"{avg_return_pct:.2f}%")
                col2.metric("Avg Discount", f"{avg_discount:.2f}")
                col3.metric("Most Returned Sub-Category", high_return_subcat)

                # --- Bubble Chart: Discount vs Return Rate ---
                st.markdown("### Discount vs Return Rate by Sub-Category")
                bubble_df = orders_filtered.groupby("Sub-Category").agg({
                    "Discount": "mean",
                    "Is Returned": "mean",
                    "Profit": "sum"
                }).reset_index()
                bubble_df["Is Returned %"] = bubble_df["Is Returned"] * 100
                bubble_df["Profit Bubble"] = bubble_df["Profit"].clip(lower=0)

                fig1 = px.scatter(
                    bubble_df, x="Discount", y="Is Returned %",
                    size="Profit Bubble", color="Profit",
                    hover_name="Sub-Category", text="Sub-Category",
                    title="Discount vs Return Rate",
                    labels={"Is Returned %": "Return Rate (%)"}
                )
                fig1.update_layout(
                    height=450,
                    margin=dict(t=50, l=10, r=10, b=20),
                    font=dict(size=16),
                    title_font=dict(size=20)
                )
                st.plotly_chart(fig1, use_container_width=True, key="bubble_returns")

                # --- Line Chart: Return Rate Over Time ---
                st.markdown("### Return Rate Over Time")
                return_trend_df = orders_filtered.copy()
                return_trend_df["Month"] = return_trend_df["Order Date"].dt.to_period("M").astype(str)
                return_monthly = return_trend_df.groupby("Month")["Is Returned"].mean().reset_index()
                return_monthly["Is Returned %"] = return_monthly["Is Returned"] * 100

                fig2 = px.line(
                    return_monthly, x="Month", y="Is Returned %",
                    title="Monthly Return Rate Trend",
                    markers=True,
                    labels={"Is Returned %": "Return Rate (%)"}
                )
                fig2.update_layout(
                    height=400,
                    font=dict(size=16),
                    title_font=dict(size=20),
                    margin=dict(t=40, l=10, r=10, b=20)
                )
                st.plotly_chart(fig2, use_container_width=True, key="return_trend")
        elif sub_tab == "AI - Ask Data Anything":
                
                st.markdown("### Have a question about Data? Ask Your Agent! ")
                st.markdown("#### Ask a business question about sales, returns, shipping, profit, customers, or performance by region or category.")

                suggested_questions = {
                    "Sales & Profit": [
                        "What is the trend of sales over the last 6 months?",
                        "Which product categories are the most profitable?",
                        "What’s the average discount for top 10 SKUs by sales?",
                    ],
                    "Returns & Operations": [
                        "Which sub-categories have the highest return rates?",
                        "Does discount correlate with returns?",
                        "Which ship mode causes the longest delivery lag?",
                    ],
                    "Region & Geo": [
                        "Which state has the highest sales?",
                        "Compare profit margins between Central and West regions.",
                        "Show return rate by region and category.",
                    ],
                    "Customers & Segments": [
                        "Which customers placed the most orders?",
                        "What is the average order value for Corporate vs Consumer?",
                        "Who are the top 5 customers by total profit?",
                    ]
                }

                # Select Category
                selected_category = st.selectbox("#### Choose a category to see suggested questions:", list(suggested_questions.keys()))
                st.write("#### Click a question below to insert into the input box or type your own question:")

                # Suggestion Buttons
                for q in suggested_questions[selected_category]:
                    if st.button(q):
                        st.session_state["ai_question"] = q
                
                user_prompt = st.text_area("Your Question", value=st.session_state.get("ai_question", ""), height=100)

                claude_api_key = os.getenv("CLAUDE_API_KEY")
                client = anthropic.Anthropic(api_key=claude_api_key)
                
                if st.button("Ask Your Agent") and user_prompt.strip():
                    with st.spinner("Generating data-backed insights from Claude..."):

                        # === Precomputed Summary Metrics ===
                        cat_sales = orders_filtered.groupby("Category")["Sales"].sum().round(2).to_dict()
                        returns_by_cat = (
                            orders_filtered.groupby("Category")["Return"]
                            .apply(lambda x: (x == "Yes").mean())
                            .round(3).to_dict()
                        )
                        profit_by_seg = orders_filtered.groupby("Segment")["Profit"].sum().round(2).to_dict()
                        top_customers = (
                            orders_filtered.groupby("Customer Name")["Profit"]
                            .sum().sort_values(ascending=False).head(5).round(2).to_dict()
                        )

                        # Region-level insights
                        sales_by_region = orders_filtered.groupby("Region")["Sales"].sum().round(2).to_dict()
                        profit_by_region = orders_filtered.groupby("Region")["Profit"].sum().round(2).to_dict()
                        return_rate_region = (
                            orders_filtered.groupby("Region")["Return"]
                            .apply(lambda x: (x == "Yes").mean())
                            .round(3).to_dict()
                        )

                        # Sub-category-level insights
                        profit_by_subcat = orders_filtered.groupby("Sub-Category")["Profit"].sum().round(2).to_dict()
                        returns_by_subcat = (
                            orders_filtered.groupby("Sub-Category")["Return"]
                            .apply(lambda x: (x == "Yes").mean())
                            .round(3).to_dict()
                        )

                        # === Prompt Assembly ===
                        summary_block = f"""
                            CATEGORY-LEVEL:
                            - Sales by Category: {cat_sales}
                            - Return Rate by Category: {returns_by_cat}
                            - Profit by Segment: {profit_by_seg}
                            - Top 5 Customers by Profit: {top_customers}

                            REGION-LEVEL:
                            - Sales by Region: {sales_by_region}
                            - Profit by Region: {profit_by_region}
                            - Return Rate by Region: {return_rate_region}

                            SUB-CATEGORY-LEVEL:
                            - Profit by Sub-Category: {profit_by_subcat}
                            - Return Rate by Sub-Category: {returns_by_subcat}
                            """

                        prompt = f"""
                        You are a business intelligence analyst AI.
                        You have access to the following aggregated dataset summaries from an e-commerce platform:

                        {summary_block}

                        Based on this data, please answer the user's business question below:
                        "{user_prompt}"

                        Provide a clear, insightful, and data-driven explanation.
                        """

                                    # === Claude API Call ===
                        try:
                                        response = client.messages.create(
                                            model="claude-sonnet-4-20250514",
                                            max_tokens=500,
                                            temperature=0.4,
                                            messages=[{"role": "user", "content": prompt}]
                                        )
                                        st.markdown("**Claude's Answer:**")
                                        st.write(response.content[0].text)
                        except Exception as e:
                                        st.error(f"Claude API Error: {e}")

        elif sub_tab == "EDA":
                st.subheader("Exploratory Data Analysis (EDA)")

                # 1️⃣ Shape & Structure
                st.markdown("### 1. Shape & Structure")
                st.write(f"**Rows:** {orders_filtered.shape[0]} | **Columns:** {orders_filtered.shape[1]}")
                st.write("**Data Types:**")
                st.write(orders_filtered.dtypes.astype(str))

                # 2️⃣ Missing Values
                st.markdown("### 2️⃣ Missing Values")
                missing_vals = orders_filtered.isnull().sum()
                st.dataframe(missing_vals[missing_vals > 0], use_container_width=True)

                # 3️⃣ Duplicates
                st.markdown("### 3️⃣ Duplicates")
                dup_count = orders_filtered.duplicated().sum()
                st.write(f"**Duplicate Rows:** {dup_count}")
                if dup_count > 0:
                    st.dataframe(orders_filtered[orders_filtered.duplicated()].head(), use_container_width=True)

                # 4️⃣ Outliers (Boxplot)
                st.markdown("### 4️⃣ Outliers")
                col1, col2, col3 = st.columns(3)
                with col1:
                    fig_box1 = px.box(orders_filtered, y="Sales", title="Sales Boxplot")
                    st.plotly_chart(fig_box1, use_container_width=True)
                with col2:
                    fig_box2 = px.box(orders_filtered, y="Profit", title="Profit Boxplot")
                    st.plotly_chart(fig_box2, use_container_width=True)
                with col3:
                    fig_box3 = px.box(orders_filtered, y="Discount", title="Discount Boxplot")
                    st.plotly_chart(fig_box3, use_container_width=True)

                # 5️⃣ Value Distributions
                st.markdown("### 5️⃣ Value Distributions")
                col4, col5 = st.columns(2)
                with col4:
                    fig_hist1 = px.histogram(orders_filtered, x="Sales", nbins=50, title="Sales Distribution")
                    st.plotly_chart(fig_hist1, use_container_width=True)
                with col5:
                    fig_hist2 = px.histogram(orders_filtered, x="Profit", nbins=50, title="Profit Distribution")
                    st.plotly_chart(fig_hist2, use_container_width=True)

                # 6️⃣ Unique Values
                st.markdown("### 6️⃣ Unique Values")
                st.write("**Unique Counts per Categorical Field:**")
                cat_cols = ["Category", "Sub-Category", "Segment", "Region", "Ship Mode"]
                st.dataframe({col: orders_filtered[col].nunique() for col in cat_cols})

                # 7️⃣ Date Range Coverage
                st.markdown("### 7️⃣ Date Range Coverage")
                min_date, max_date = orders_filtered["Order Date"].min(), orders_filtered["Order Date"].max()
                st.write(f"**Order Date Range:** {min_date} → {max_date}")

                # 8️⃣ Invalid Entries
                st.markdown("### 8️⃣ Invalid Entries")
                st.write(f"**Negative Profit Rows:** {len(orders_filtered[orders_filtered['Profit'] < 0])}")
                st.write(f"**Discount > 100% Rows:** {len(orders_filtered[orders_filtered['Discount'] > 1.0])}")
                if len(orders_filtered[orders_filtered["Discount"] > 1.0]) > 0:
                    st.dataframe(orders_filtered[orders_filtered["Discount"] > 1.0].head(5))

                # 9️⃣ Correlations
                st.markdown("### 9️⃣ Correlation Heatmap")
                corr = orders_filtered[["Sales", "Profit", "Discount", "Quantity"]].corr()
                fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
                st.plotly_chart(fig_corr, use_container_width=True)

                # 🔟 Top-K Patterns
                st.markdown("### 🔟 Top-K Patterns")
                top_products = orders_filtered.groupby("Product Name")["Sales"].sum().nlargest(10).reset_index()
                top_customers = orders_filtered.groupby("Customer Name")["Sales"].sum().nlargest(10).reset_index()
                top_cities = orders_filtered.groupby("City")["Sales"].sum().nlargest(10).reset_index()
                col6, col7, col8 = st.columns(3)
                with col6:
                    fig_prod = px.bar(top_products, x="Sales", y="Product Name", orientation="h", title="Top Products by Sales")
                    st.plotly_chart(fig_prod, use_container_width=True)
                with col7:
                    fig_cust = px.bar(top_customers, x="Sales", y="Customer Name", orientation="h", title="Top Customers by Sales")
                    st.plotly_chart(fig_cust, use_container_width=True)
                with col8:
                    fig_city = px.bar(top_cities, x="Sales", y="City", orientation="h", title="Top Cities by Sales")
                    st.plotly_chart(fig_city, use_container_width=True)

                # ✅ Summary/Flag Report
                st.markdown("### Summary/Flag Report")
                flags = []
                if dup_count > 0:
                    flags.append("Duplicates exist.")
                if missing_vals.sum() > 0:
                    flags.append("Missing values found.")
                if len(orders_filtered[orders_filtered["Discount"] > 1.0]) > 0:
                    flags.append("Discounts over 100%.")
                if len(orders_filtered[orders_filtered["Profit"] < 0]) > 0:
                    flags.append("Negative profit rows detected.")

                if not flags:
                    st.success("Dataset passes all quality checks!")
                else:
                    st.warning("### Flags Raised")
                    for f in flags:
                        st.write(f)
        elif sub_tab== "Predict Return":
                st.subheader("Predict Returns")

                # Load model
                model = joblib.load("models/return_classifier_xgboost.joblib")

                try:
                    with open("models/xgboost_feature_names.json") as f:
                        feature_cols = json.load(f)
                except FileNotFoundError:
                    feature_cols = model.feature_names_in_ if hasattr(model, "feature_names_in_") else None

                # User input form
                st.markdown("### Try a New Prediction")
                user_input = {}
                for col in ["Category", "Sub-Category", "Segment", "Region"]:
                    user_input[col] = st.selectbox(col, sorted(orders_filtered[col].unique()), key=f"form_{col}")
                for col in ["Sales", "Discount"]:
                    user_input[col] = st.number_input(col, value=float(orders_filtered[col].median()), key=f"form_{col}_num")

                input_df = pd.DataFrame([user_input])
                input_encoded = pd.get_dummies(input_df)

                # Align with model's expected columns
                if feature_cols:
                    input_encoded = input_encoded.reindex(columns=feature_cols, fill_value=0)

                prediction = model.predict(input_encoded)[0]
                prediction_label = 'Item will mostly probably Be Returned' if prediction == 1 else 'Item most probably Will Not Be Returned'
                st.success(f"**Prediction:** {prediction_label}")

                # SHAP narrative (prewritten)
                st.markdown("### What Drives Returns?")
                st.markdown("""
                Insights derived from SHAP explainability analysis:
                - **High discounts (>30%)** significantly increase return risk.
                - **Technology** and **Office Supplies** categories are return-prone.
                - **Consumer** segment sees higher return rates than others.
                - Low sales value combined with high discount is a common return pattern.
                """)
                try:
                    shap_df = pd.read_csv("models/shap_top_features.csv")
                    st.markdown("### Returns Important Features from our data")

                    # Create a dynamic narrative from top 3–5 features
                    top_n = 5
                    insights = []
                    for i, row in shap_df.head(top_n).iterrows():
                        feature = row['feature'].replace("_", " ")
                        importance = row['importance']
                        direction = "increases" if "Discount" in feature or "Consumer" in feature else "impacts"
                        insights.append(f"- **{feature}** strongly {direction} return risk (SHAP weight: {importance:.2f})")

                    st.markdown("\n".join(insights))

                    # Plot bar chart
                    st.markdown("#### 🔍 Top Return-Driving Features:")
                    st.bar_chart(shap_df.set_index("feature")["importance"])

                except FileNotFoundError:
                    st.warning("SHAP feature importance file not found.")
        elif sub_tab == "Predict Profits":
                st.subheader("Predict Profit")

                # --- Load model and feature names ---
                model = joblib.load("models/profit_regressor_xgb.joblib")
                with open("models/profit_feature_names.json") as f:
                    profit_features = json.load(f)

                # --- Input form ---
                st.markdown("### Enter Order Details:")
                profit_input = {}
                for col in ["Category", "Sub-Category", "Segment", "Region"]:
                    profit_input[col] = st.selectbox(col, sorted(orders_filtered[col].unique()), key=f"profit_sel_{col}")
                for col in ["Sales", "Discount", "Quantity"]:
                    default_val = float(orders_filtered[col].median())
                    profit_input[col] = st.number_input(col, value=default_val, key=f"profit_num_{col}")

                input_df = pd.DataFrame([profit_input])
                input_encoded = pd.get_dummies(input_df)
                input_encoded = input_encoded.reindex(columns=profit_features, fill_value=0)

                # --- Prediction ---
                pred_profit = model.predict(input_encoded)[0]
                st.success(f"Predicted Profit: **${pred_profit:,.2f}**")

                # --- SHAP Insights ---
                st.markdown("### Top Factors Driving Profit")
                try:
                    shap_df = pd.read_csv("models/shap_profit_top_features.csv").set_index("feature")
                    st.bar_chart(shap_df["importance"])

                    st.markdown("#### Insights:")
                    for feature, row in shap_df.iterrows():
                        insight = f"- **{feature.replace('_', ' ')}** contributes ~{row['importance']:.2f} SHAP impact to profit."
                        st.markdown(insight)
                except FileNotFoundError:
                    st.warning("SHAP feature summary not found. Please generate 'shap_profit_top_features.csv'.")