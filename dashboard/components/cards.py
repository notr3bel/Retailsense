"""
Reusable KPI Cards & Metric Widgets for RetailSense-AI Streamlit Dashboard.
"""

from typing import Optional, Dict, Any
import streamlit as st


def format_currency(val: float) -> str:
    """Formats floating point values into clean currency strings ($M, $K, $)."""
    if val >= 1_000_000:
        return f"${val / 1_000_000:.2f}M"
    elif val >= 1_000:
        return f"${val / 1_000:.1f}K"
    else:
        return f"${val:.2f}"


def format_number(val: int) -> str:
    """Formats numbers with comma separators or M/K suffixes."""
    if val >= 1_000_000:
        return f"{val / 1_000_000:.2f}M"
    elif val >= 1_000:
        return f"{val / 1_000:.1f}K"
    else:
        return f"{val:,}"


def render_kpi_card(
    title: str,
    value: str,
    subtitle: str = "",
    icon: str = "📊",
    col: Optional[Any] = None
) -> None:
    """
    Renders a responsive, glassmorphic KPI Card.
    """
    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-card-header">
            <span>{title}</span>
            <span class="kpi-card-icon">{icon}</span>
        </div>
        <div class="kpi-card-value">{value}</div>
        <div class="kpi-card-sub">{subtitle}</div>
    </div>
    """
    if col:
        col.markdown(card_html, unsafe_allow_html=True)
    else:
        st.markdown(card_html, unsafe_allow_html=True)


def render_executive_kpis(metrics: Dict[str, Any]) -> None:
    """
    Renders 6 executive KPI cards in a responsive layout grid.
    
    Card 1: Total Revenue
    Card 2: Total Orders
    Card 3: Total Customers
    Card 4: Total Products
    Card 5: Average Order Value
    Card 6: Total Countries
    """
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    rev_str = format_currency(metrics.get("total_revenue", 0.0))
    orders_str = format_number(metrics.get("total_orders", 0))
    cust_str = format_number(metrics.get("total_customers", 0))
    prod_str = format_number(metrics.get("total_products", 0))
    aov_str = format_currency(metrics.get("average_order_value", 0.0))
    country_str = str(metrics.get("total_countries", 0))

    render_kpi_card("Total Revenue", rev_str, "Gross Revenue Generated", "💰", col1)
    render_kpi_card("Total Orders", orders_str, "Unique Completed Orders", "📦", col2)
    render_kpi_card("Total Customers", cust_str, "Active Buyer Profiles", "👥", col3)
    render_kpi_card("Total Products", prod_str, "Active Product Catalog", "🛍️", col4)
    render_kpi_card("Avg Order Value", aov_str, "Revenue per Invoice", "💳", col5)
    render_kpi_card("Countries", country_str, "Global Retail Reach", "🌍", col6)


def render_pipeline_status_card(metadata: Dict[str, Any], col: Optional[Any] = None) -> None:
    """
    Renders a compact pipeline status card displaying execution metrics.
    """
    status = metadata.get("status", "UNKNOWN").upper()
    exec_date = metadata.get("execution_date", metadata.get("end_time", "N/A"))
    if isinstance(exec_date, str) and "T" in exec_date:
        exec_date = exec_date.split("T")[0] + " " + exec_date.split("T")[1][:5]
    duration = metadata.get("duration", "N/A")
    version = metadata.get("pipeline_version", "1.0.0")

    badge_class = "status-badge-success" if status in ["SUCCESS", "SUCCESSFUL"] else "status-badge-danger"
    dot_class = "pulse-dot-green" if status in ["SUCCESS", "SUCCESSFUL"] else "pulse-dot-red"

    card_html = f"""
    <div class="kpi-card" style="border-left: 4px solid #6366f1;">
        <div class="kpi-card-header">
            <span>Airflow MLOps Pipeline</span>
            <span class="status-badge {badge_class}">
                <span class="pulse-dot {dot_class}"></span> {status}
            </span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.85rem; color: #cbd5e1;">
            <div><strong>Last Run:</strong> {exec_date}</div>
            <div><strong>Duration:</strong> {duration}</div>
            <div><strong>Version:</strong> v{version}</div>
        </div>
    </div>
    """
    if col:
        col.markdown(card_html, unsafe_allow_html=True)
    else:
        st.markdown(card_html, unsafe_allow_html=True)
