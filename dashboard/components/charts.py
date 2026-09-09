"""
Plotly Chart Builders for RetailSense-AI Streamlit Dashboard.
Provides reusable dark-themed BI visualizations.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# Global Dark Theme Layout Configuration
DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15, 23, 42, 0.5)",
    font=dict(family="Inter, sans-serif", color="#cbd5e1", size=12),
    margin=dict(l=40, r=40, t=50, b=40),
    xaxis=dict(
        showgrid=True,
        gridcolor="rgba(255, 255, 255, 0.06)",
        zerolinecolor="rgba(255, 255, 255, 0.1)",
        tickfont=dict(color="#94a3b8")
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="rgba(255, 255, 255, 0.06)",
        zerolinecolor="rgba(255, 255, 255, 0.1)",
        tickfont=dict(color="#94a3b8")
    ),
    legend=dict(
        bgcolor="rgba(30, 41, 59, 0.5)",
        bordercolor="rgba(255, 255, 255, 0.1)",
        font=dict(color="#f8fafc")
    )
)

ACCENT_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#3b82f6"]


# ----------------------------------------------------
# HOME & SALES CHARTS
# ----------------------------------------------------

def plot_monthly_revenue_trend(df: pd.DataFrame) -> go.Figure:
    """Monthly Revenue Trend Line & Area Chart."""
    if df is None or df.empty:
        return go.Figure()

    if "year_month" in df.columns:
        df_monthly = df.groupby("year_month")["total_price"].sum().reset_index()
        df_monthly = df_monthly.sort_values("year_month")
        x_col, y_col = "year_month", "total_price"
    elif "year" in df.columns and "month" in df.columns:
        df_monthly = df.groupby(["year", "month"])["total_revenue"].sum().reset_index()
        df_monthly["period"] = df_monthly["year"].astype(str) + "-" + df_monthly["month"].astype(str).str.zfill(2)
        df_monthly = df_monthly.sort_values("period")
        x_col, y_col = "period", "total_revenue"
    else:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_monthly[x_col],
            y=df_monthly[y_col],
            mode="lines+markers",
            name="Revenue",
            line=dict(color="#6366f1", width=3, shape="spline"),
            marker=dict(size=7, color="#818cf8", borderwidth=2, bordercolor="#ffffff"),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.15)",
            hovertemplate="<b>Period:</b> %{x}<br><b>Revenue:</b> $%{y:,.2f}<extra></extra>"
        )
    )
    fig.update_layout(
        title=dict(text="📈 Monthly Revenue Trend", font=dict(size=16, color="#f8fafc")),
        xaxis_title="Period",
        yaxis_title="Revenue ($)",
        **DARK_LAYOUT
    )
    return fig


def plot_monthly_orders(df: pd.DataFrame) -> go.Figure:
    """Monthly Orders Bar Chart."""
    if df is None or df.empty:
        return go.Figure()

    inv_col = "invoice_no" if "invoice_no" in df.columns else ("invoice" if "invoice" in df.columns else None)
    if "year_month" in df.columns and inv_col:
        df_orders = df.groupby("year_month")[inv_col].nunique().reset_index()
        df_orders.columns = ["period", "orders"]
    elif "year" in df.columns and "total_orders" in df.columns:
        df_orders = df.copy()
        df_orders["period"] = df_orders["year"].astype(str) + "-" + df_orders["month"].astype(str).str.zfill(2)
        df_orders = df_orders.rename(columns={"total_orders": "orders"})
    else:
        return go.Figure()

    df_orders = df_orders.sort_values("period")

    fig = px.bar(
        df_orders,
        x="period",
        y="orders",
        title="📦 Monthly Order Volume",
        color_discrete_sequence=["#10b981"]
    )
    fig.update_traces(
        hovertemplate="<b>Period:</b> %{x}<br><b>Orders:</b> %{y:,}<extra></extra>",
        marker_line_color="rgba(255,255,255,0.2)",
        marker_line_width=1
    )
    fig.update_layout(
        xaxis_title="Period",
        yaxis_title="Total Orders",
        **DARK_LAYOUT
    )
    return fig


def plot_revenue_growth(df: pd.DataFrame) -> go.Figure:
    """Month-over-Month Revenue Growth Percentage."""
    if df is None or df.empty:
        return go.Figure()

    if "year_month" in df.columns:
        df_monthly = df.groupby("year_month")["total_price"].sum().reset_index()
        df_monthly.columns = ["period", "revenue"]
    elif "year" in df.columns:
        df_monthly = df.copy()
        df_monthly["period"] = df_monthly["year"].astype(str) + "-" + df_monthly["month"].astype(str).str.zfill(2)
        df_monthly = df_monthly.rename(columns={"total_revenue": "revenue"})
    else:
        return go.Figure()

    df_monthly = df_monthly.sort_values("period")
    df_monthly["growth_pct"] = df_monthly["revenue"].pct_change() * 100

    colors = ["#10b981" if g >= 0 else "#ef4444" for g in df_monthly["growth_pct"].fillna(0)]

    fig = go.Figure(
        go.Bar(
            x=df_monthly["period"],
            y=df_monthly["growth_pct"],
            marker_color=colors,
            hovertemplate="<b>Period:</b> %{x}<br><b>MoM Growth:</b> %{y:+.2f}%<extra></extra>"
        )
    )
    fig.update_layout(
        title=dict(text="📊 Month-over-Month Revenue Growth (%)", font=dict(size=16, color="#f8fafc")),
        xaxis_title="Period",
        yaxis_title="Growth (%)",
        **DARK_LAYOUT
    )
    return fig


def plot_revenue_by_weekday(df: pd.DataFrame) -> go.Figure:
    """Revenue Breakdown by Day of the Week."""
    if df is None or "weekday" not in df.columns:
        return go.Figure()

    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df_day = df.groupby("weekday")["total_price"].sum().reindex(days_order).dropna().reset_index()

    fig = px.bar(
        df_day,
        x="weekday",
        y="total_price",
        title="📅 Revenue by Day of the Week",
        color="total_price",
        color_continuous_scale="Purples"
    )
    fig.update_traces(hovertemplate="<b>Day:</b> %{x}<br><b>Revenue:</b> $%{y:,.2f}<extra></extra>")
    fig.update_layout(
        xaxis_title="Weekday",
        yaxis_title="Revenue ($)",
        coloraxis_showscale=False,
        **DARK_LAYOUT
    )
    return fig


def plot_revenue_by_hour(df: pd.DataFrame) -> go.Figure:
    """Hourly Revenue Distribution."""
    if df is None or "hour" not in df.columns:
        return go.Figure()

    df_hour = df.groupby("hour")["total_price"].sum().reset_index()

    fig = px.area(
        df_hour,
        x="hour",
        y="total_price",
        title="⏰ Hourly Sales Velocity (Peak Hours)",
        color_discrete_sequence=["#06b6d4"]
    )
    fig.update_traces(hovertemplate="<b>Hour:</b> %{x}:00<br><b>Revenue:</b> $%{y:,.2f}<extra></extra>")
    fig.update_layout(
        xaxis=dict(tickmode="linear", tick0=0, dtick=1),
        xaxis_title="Hour of Day (24h)",
        yaxis_title="Revenue ($)",
        **DARK_LAYOUT
    )
    return fig


def plot_moving_average_revenue(df: pd.DataFrame, window: int = 3) -> go.Figure:
    """Moving Average Revenue Trend."""
    if df is None or df.empty:
        return go.Figure()

    if "year_month" in df.columns:
        df_monthly = df.groupby("year_month")["total_price"].sum().reset_index()
        df_monthly.columns = ["period", "revenue"]
    else:
        return go.Figure()

    df_monthly = df_monthly.sort_values("period")
    df_monthly["ma"] = df_monthly["revenue"].rolling(window=window, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_monthly["period"],
            y=df_monthly["revenue"],
            name="Monthly Revenue",
            marker_color="rgba(99, 102, 241, 0.4)"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_monthly["period"],
            y=df_monthly["ma"],
            mode="lines+markers",
            name=f"{window}-Month Moving Avg",
            line=dict(color="#f59e0b", width=3)
        )
    )
    fig.update_layout(
        title=dict(text=f"📉 Revenue Trend & {window}-Month Moving Average", font=dict(size=16, color="#f8fafc")),
        xaxis_title="Period",
        yaxis_title="Revenue ($)",
        **DARK_LAYOUT
    )
    return fig


# ----------------------------------------------------
# PRODUCT CHARTS
# ----------------------------------------------------

def plot_top_products(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Top N Products by Revenue."""
    if df is None or df.empty:
        return go.Figure()

    if "stock_code" in df.columns and "total_price" in df.columns:
        df_top = df.groupby(["stock_code", "description"])["total_price"].sum().reset_index()
        df_top = df_top.sort_values("total_price", ascending=False).head(top_n)
        df_top["label"] = df_top["description"].str.slice(0, 30)
    elif "stock_code" in df.columns and "total_revenue" in df.columns:
        df_top = df.sort_values("total_revenue", ascending=False).head(top_n)
        df_top["label"] = df_top["description"].str.slice(0, 30)
        df_top["total_price"] = df_top["total_revenue"]
    else:
        return go.Figure()

    fig = px.bar(
        df_top.sort_values("total_price", ascending=True),
        x="total_price",
        y="label",
        orientation="h",
        title=f"🏆 Top {top_n} Products by Revenue",
        color="total_price",
        color_continuous_scale="Blues"
    )
    fig.update_traces(hovertemplate="<b>Product:</b> %{y}<br><b>Revenue:</b> $%{x:,.2f}<extra></extra>")
    fig.update_layout(
        xaxis_title="Revenue ($)",
        yaxis_title="Product Description",
        coloraxis_showscale=False,
        **DARK_LAYOUT
    )
    return fig


def plot_revenue_by_category(df: pd.DataFrame) -> go.Figure:
    """Revenue Breakdown by Category."""
    if df is None or "category" not in df.columns:
        return go.Figure()

    rev_col = "total_revenue" if "total_revenue" in df.columns else "total_price"
    df_cat = df.groupby("category")[rev_col].sum().reset_index().sort_values(rev_col, ascending=False)

    fig = px.bar(
        df_cat,
        x="category",
        y=rev_col,
        title="🏷️ Revenue by Product Category",
        color="category",
        color_discrete_sequence=ACCENT_COLORS
    )
    fig.update_traces(hovertemplate="<b>Category:</b> %{x}<br><b>Revenue:</b> $%{y:,.2f}<extra></extra>")
    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Revenue ($)",
        showlegend=False,
        **DARK_LAYOUT
    )
    return fig


def plot_quantity_sold(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Top Products by Quantity Sold."""
    if df is None or df.empty:
        return go.Figure()

    qty_col = "quantity" if "quantity" in df.columns else "total_quantity_sold"
    if qty_col not in df.columns:
        return go.Figure()

    df_qty = df.groupby("description")[qty_col].sum().reset_index()
    df_qty = df_qty.sort_values(qty_col, ascending=False).head(top_n)
    df_qty["label"] = df_qty["description"].str.slice(0, 30)

    fig = px.bar(
        df_qty.sort_values(qty_col, ascending=True),
        x=qty_col,
        y="label",
        orientation="h",
        title=f"📦 Top {top_n} Products by Quantity Sold",
        color_discrete_sequence=["#8b5cf6"]
    )
    fig.update_traces(hovertemplate="<b>Product:</b> %{y}<br><b>Units Sold:</b> %{x:,}<extra></extra>")
    fig.update_layout(
        xaxis_title="Units Sold",
        yaxis_title="Product",
        **DARK_LAYOUT
    )
    return fig


def plot_pareto_chart(df: pd.DataFrame) -> go.Figure:
    """Pareto Analysis (80/20 Cumulative Revenue Rule)."""
    if df is None or df.empty:
        return go.Figure()

    rev_col = "total_revenue" if "total_revenue" in df.columns else "total_price"
    if rev_col not in df.columns:
        return go.Figure()

    df_sorted = df.groupby("description")[rev_col].sum().reset_index().sort_values(rev_col, ascending=False)
    df_sorted["cum_revenue"] = df_sorted[rev_col].cumsum()
    df_sorted["cum_pct"] = (df_sorted["cum_revenue"] / df_sorted[rev_col].sum()) * 100
    df_top = df_sorted.head(20)
    df_top["label"] = df_top["description"].str.slice(0, 25)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_top["label"],
            y=df_top[rev_col],
            name="Revenue",
            marker_color="#6366f1"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_top["label"],
            y=df_top["cum_pct"],
            name="Cumulative %",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#ec4899", width=3)
        )
    )
    fig.update_layout(
        title=dict(text="📊 Pareto Product Analysis (Cumulative Revenue %)", font=dict(size=16, color="#f8fafc")),
        xaxis=dict(title="Products (Top 20)", tickangle=-45),
        yaxis=dict(title="Revenue ($)"),
        yaxis2=dict(title="Cumulative Revenue %", overlaying="y", side="right", range=[0, 105]),
        **DARK_LAYOUT
    )
    return fig


def plot_category_distribution(df: pd.DataFrame) -> go.Figure:
    """Product Category Share Donut Chart."""
    if df is None or "category" not in df.columns:
        return go.Figure()

    rev_col = "total_revenue" if "total_revenue" in df.columns else "total_price"
    df_cat = df.groupby("category")[rev_col].sum().reset_index()

    fig = px.pie(
        df_cat,
        values=rev_col,
        names="category",
        hole=0.5,
        title="🍩 Category Revenue Share",
        color_discrete_sequence=ACCENT_COLORS
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>Category:</b> %{label}<br><b>Revenue:</b> $%{value:,.2f}<extra></extra>"
    )
    fig.update_layout(**DARK_LAYOUT)
    return fig


# ----------------------------------------------------
# CUSTOMER CHARTS
# ----------------------------------------------------

def plot_top_customers(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Top N Customers by Lifetime Spend."""
    if df is None or df.empty:
        return go.Figure()

    cust_col = "customer_id" if "customer_id" in df.columns else "CustomerID"
    spent_col = "total_spent" if "total_spent" in df.columns else "total_price"

    df_top = df.groupby(cust_col)[spent_col].sum().reset_index().sort_values(spent_col, ascending=False).head(top_n)
    df_top[cust_col] = "ID: " + df_top[cust_col].astype(str).str.replace(".0", "", regex=False)

    fig = px.bar(
        df_top.sort_values(spent_col, ascending=True),
        x=spent_col,
        y=cust_col,
        orientation="h",
        title=f"👑 Top {top_n} Customers by Total Spent",
        color_discrete_sequence=["#f59e0b"]
    )
    fig.update_traces(hovertemplate="<b>Customer:</b> %{y}<br><b>Total Spent:</b> $%{x:,.2f}<extra></extra>")
    fig.update_layout(
        xaxis_title="Total Spent ($)",
        yaxis_title="Customer ID",
        **DARK_LAYOUT
    )
    return fig


def plot_clv_distribution(df: pd.DataFrame) -> go.Figure:
    """Customer Lifetime Value (CLV) Histogram."""
    if df is None or df.empty:
        return go.Figure()

    spent_col = "total_spent" if "total_spent" in df.columns else "total_price"
    if spent_col not in df.columns:
        return go.Figure()

    # Log transform or cap for readable visualization
    spent_data = df[spent_col][df[spent_col] > 0]

    fig = px.histogram(
        spent_data,
        x=spent_col,
        nbins=40,
        title="💰 Customer Lifetime Value (CLV) Distribution",
        color_discrete_sequence=["#10b981"],
        log_y=True
    )
    fig.update_traces(hovertemplate="<b>Spend Range:</b> $%{x:,.2f}<br><b>Customers:</b> %{y}<extra></extra>")
    fig.update_layout(
        xaxis_title="Customer Lifetime Value ($)",
        yaxis_title="Customer Count (Log Scale)",
        **DARK_LAYOUT
    )
    return fig


def plot_repeat_vs_new(df: pd.DataFrame) -> go.Figure:
    """Repeat vs One-Time Customers Ratio."""
    if df is None or df.empty:
        return go.Figure()

    inv_col = "invoice_no" if "invoice_no" in df.columns else ("invoice" if "invoice" in df.columns else None)
    orders_col = "total_orders" if "total_orders" in df.columns else inv_col
    cust_col = "customer_id" if "customer_id" in df.columns else "CustomerID"

    if orders_col in ["invoice_no", "invoice"]:
        df_orders = df.groupby(cust_col)[orders_col].nunique().reset_index()
        df_orders.columns = ["customer_id", "orders"]
    else:
        df_orders = df[[cust_col, orders_col]].copy()
        df_orders.columns = ["customer_id", "orders"]

    repeat_count = (df_orders["orders"] > 1).sum()
    single_count = (df_orders["orders"] == 1).sum()

    df_pie = pd.DataFrame({
        "Customer Type": ["Repeat Buyers (>1 Order)", "One-Time Buyers (1 Order)"],
        "Count": [repeat_count, single_count]
    })

    fig = px.pie(
        df_pie,
        values="Count",
        names="Customer Type",
        hole=0.45,
        title="🔄 Repeat vs. One-Time Buyers",
        color_discrete_sequence=["#6366f1", "#94a3b8"]
    )
    fig.update_traces(textinfo="percent+label", hovertemplate="<b>Type:</b> %{label}<br><b>Count:</b> %{value:,}<extra></extra>")
    fig.update_layout(**DARK_LAYOUT)
    return fig


def plot_avg_basket_size(df: pd.DataFrame) -> go.Figure:
    """Average Basket Size Distribution."""
    if df is None or df.empty:
        return go.Figure()

    inv_col = "invoice_no" if "invoice_no" in df.columns else ("invoice" if "invoice" in df.columns else None)
    if "average_items_per_order" in df.columns:
        basket_data = df["average_items_per_order"]
    elif "quantity" in df.columns and inv_col:
        basket_data = df.groupby(inv_col)["quantity"].sum()
    else:
        return go.Figure()

    fig = px.box(
        basket_data,
        y=basket_data.values,
        title="🛒 Average Basket Size (Items per Order)",
        color_discrete_sequence=["#3b82f6"]
    )
    fig.update_layout(
        yaxis_title="Items per Order",
        **DARK_LAYOUT
    )
    return fig


def plot_rfm_summary(df: pd.DataFrame) -> go.Figure:
    """RFM Scatter Plot (Frequency vs Spend)."""
    if df is None or df.empty:
        return go.Figure()

    spent_col = "total_spent" if "total_spent" in df.columns else "total_price"
    inv_col = "invoice_no" if "invoice_no" in df.columns else ("invoice" if "invoice" in df.columns else None)
    orders_col = "total_orders" if "total_orders" in df.columns else inv_col

    if orders_col in ["invoice_no", "invoice"]:
        df_rfm = df.groupby("customer_id").agg(
            frequency=(orders_col, "nunique"),
            monetary=(spent_col, "sum")
        ).reset_index()
    else:
        df_rfm = df[["customer_id", orders_col, spent_col]].copy()
        df_rfm.columns = ["customer_id", "frequency", "monetary"]

    fig = px.scatter(
        df_rfm,
        x="frequency",
        y="monetary",
        title="🎯 RFM Segmentation: Order Frequency vs. Monetary Value",
        color="monetary",
        color_continuous_scale="Viridis",
        size_max=15
    )
    fig.update_traces(hovertemplate="<b>Frequency:</b> %{x} orders<br><b>Total Spent:</b> $%{y:,.2f}<extra></extra>")
    fig.update_layout(
        xaxis_title="Order Frequency (Number of Invoices)",
        yaxis_title="Monetary Value ($)",
        coloraxis_showscale=False,
        **DARK_LAYOUT
    )
    return fig


# ----------------------------------------------------
# COUNTRY CHARTS
# ----------------------------------------------------

def plot_country_map(df: pd.DataFrame) -> go.Figure:
    """Choropleth Map of Revenue by Country."""
    if df is None or "country" not in df.columns:
        return go.Figure()

    rev_col = "total_revenue" if "total_revenue" in df.columns else "total_price"
    df_c = df.groupby("country")[rev_col].sum().reset_index()

    fig = px.choropleth(
        df_c,
        locations="country",
        locationmode="country names",
        color=rev_col,
        hover_name="country",
        title="🌍 Global Revenue Map",
        color_continuous_scale="Plasma"
    )
    fig.update_layout(
        geo=dict(
            bgcolor="rgba(0,0,0,0)",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#334155",
            projection_type="equirectangular"
        ),
        **DARK_LAYOUT
    )
    return fig


def plot_revenue_by_country(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Bar Chart of Revenue by Country."""
    if df is None or "country" not in df.columns:
        return go.Figure()

    rev_col = "total_revenue" if "total_revenue" in df.columns else "total_price"
    df_c = df.groupby("country")[rev_col].sum().reset_index().sort_values(rev_col, ascending=False).head(top_n)

    fig = px.bar(
        df_c.sort_values(rev_col, ascending=True),
        x=rev_col,
        y="country",
        orientation="h",
        title=f"🌐 Top {top_n} Countries by Revenue",
        color=rev_col,
        color_continuous_scale="Tealgrn"
    )
    fig.update_traces(hovertemplate="<b>Country:</b> %{y}<br><b>Revenue:</b> $%{x:,.2f}<extra></extra>")
    fig.update_layout(
        xaxis_title="Revenue ($)",
        yaxis_title="Country",
        coloraxis_showscale=False,
        **DARK_LAYOUT
    )
    return fig


def plot_orders_by_country(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Orders by Country."""
    if df is None or "country" not in df.columns:
        return go.Figure()

    inv_col = "invoice_no" if "invoice_no" in df.columns else ("invoice" if "invoice" in df.columns else None)
    ord_col = "total_orders" if "total_orders" in df.columns else inv_col
    if ord_col in ["invoice_no", "invoice"]:
        df_c = df.groupby("country")[ord_col].nunique().reset_index().sort_values(ord_col, ascending=False).head(top_n)
        y_col = ord_col
    else:
        df_c = df.groupby("country")["total_orders"].sum().reset_index().sort_values("total_orders", ascending=False).head(top_n)
        y_col = "total_orders"

    fig = px.bar(
        df_c,
        x="country",
        y=y_col,
        title=f"📦 Top {top_n} Countries by Order Volume",
        color_discrete_sequence=["#3b82f6"]
    )
    fig.update_traces(hovertemplate="<b>Country:</b> %{x}<br><b>Orders:</b> %{y:,}<extra></extra>")
    fig.update_layout(
        xaxis_title="Country",
        yaxis_title="Total Orders",
        **DARK_LAYOUT
    )
    return fig


def plot_customers_by_country(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Customers by Country."""
    if df is None or "country" not in df.columns:
        return go.Figure()

    cust_col = "customers" if "customers" in df.columns else "customer_id"
    if cust_col == "customer_id":
        df_c = df.groupby("country")["customer_id"].nunique().reset_index().sort_values("customer_id", ascending=False).head(top_n)
        y_col = "customer_id"
    else:
        df_c = df.groupby("country")["customers"].sum().reset_index().sort_values("customers", ascending=False).head(top_n)
        y_col = "customers"

    fig = px.bar(
        df_c,
        x="country",
        y=y_col,
        title=f"👥 Top {top_n} Countries by Customer Count",
        color_discrete_sequence=["#10b981"]
    )
    fig.update_traces(hovertemplate="<b>Country:</b> %{x}<br><b>Customers:</b> %{y:,}<extra></extra>")
    fig.update_layout(
        xaxis_title="Country",
        yaxis_title="Total Customers",
        **DARK_LAYOUT
    )
    return fig


# ----------------------------------------------------
# PIPELINE & DATA QUALITY CHARTS
# ----------------------------------------------------

def plot_pipeline_gauge(val: float, max_val: float = 100.0, title: str = "Data Quality Score") -> go.Figure:
    """Gauge Chart for MLOps Pipeline Metrics."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=val,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 14, 'color': '#f8fafc'}},
            number={'suffix': "%", 'font': {'color': '#ffffff', 'size': 24}},
            gauge={
                'axis': {'range': [0, max_val], 'tickwidth': 1, 'tickcolor': "#475569"},
                'bar': {'color': "#6366f1"},
                'bgcolor': "rgba(30, 41, 59, 0.5)",
                'bordercolor': "rgba(255, 255, 255, 0.1)",
                'steps': [
                    {'range': [0, 60], 'color': 'rgba(239, 68, 68, 0.2)'},
                    {'range': [60, 85], 'color': 'rgba(245, 158, 11, 0.2)'},
                    {'range': [85, 100], 'color': 'rgba(16, 185, 129, 0.2)'}
                ]
            }
        )
    )
    fig.update_layout(height=220, **DARK_LAYOUT)
    return fig


def plot_pipeline_timeline() -> go.Figure:
    """Pipeline Task Execution Flow Gantt/Timeline Chart."""
    tasks = [
        dict(Task="extract_data", Start=0, Finish=2, Status="Success"),
        dict(Task="validate_data", Start=2, Finish=5, Status="Success"),
        dict(Task="transform_data", Start=5, Finish=12, Status="Success"),
        dict(Task="load_postgres", Start=12, Finish=18, Status="Success"),
        dict(Task="generate_gold_layer", Start=18, Finish=22, Status="Success"),
        dict(Task="generate_reports", Start=22, Finish=24, Status="Success"),
        dict(Task="pipeline_metadata", Start=24, Finish=25, Status="Success"),
        dict(Task="success_notification", Start=25, Finish=26, Status="Success"),
    ]

    df_tasks = pd.DataFrame(tasks)

    fig = px.timeline(
        df_tasks,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Status",
        color_discrete_map={"Success": "#10b981"},
        title="⏱️ Airflow Task Execution Sequence (Seconds)"
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        xaxis_title="Execution Timeline (s)",
        yaxis_title="DAG Task",
        **DARK_LAYOUT
    )
    return fig
