"""
Sidebar Component for RetailSense-AI Streamlit Dashboard.
Provides branding, navigation, global filters (Country, Year, Month), and dataset status indicators.
"""

from typing import Dict, Any, List
import pandas as pd
import streamlit as st


def render_sidebar(datasets: Dict[str, pd.DataFrame], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Renders the sidebar navigation header, branding, and global filters.
    
    Args:
        datasets: Dict of analytical dataframes.
        metadata: Dict of pipeline execution metadata.
        
    Returns:
        Dict[str, Any]: Selected filter dictionary {"country": str, "years": List[int], "months": List[int]}.
    """
    with st.sidebar:
        # Branding Header
        st.markdown(
            """
            <div style="text-align: center; padding: 10px 0 20px 0;">
                <div style="font-size: 2.2rem; font-weight: 800; color: #818cf8;">🛍️ RetailSense</div>
                <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px;">
                    Enterprise MLOps & BI Engine
                </div>
            </div>
            <hr style="border: 0; height: 1px; background: rgba(255,255,255,0.1); margin-bottom: 20px;" />
            """,
            unsafe_allow_html=True
        )

        st.markdown("### 🎛️ Global Dashboard Filters")

        # Derive available filter options from datasets
        available_countries = ["All Countries"]
        available_years = [2009, 2010, 2011]
        available_months = list(range(1, 13))

        df_proc = datasets.get("processed")
        if df_proc is not None and not df_proc.empty:
            if "country" in df_proc.columns:
                unique_countries = sorted(df_proc["country"].dropna().unique().tolist())
                available_countries.extend(unique_countries)
            if "year" in df_proc.columns:
                available_years = sorted(df_proc["year"].dropna().astype(int).unique().tolist())
            if "month" in df_proc.columns:
                available_months = sorted(df_proc["month"].dropna().astype(int).unique().tolist())
        elif datasets.get("country_summary") is not None:
            c_df = datasets.get("country_summary")
            unique_countries = sorted(c_df["country"].dropna().unique().tolist())
            available_countries.extend(unique_countries)

        # Country Filter
        selected_country = st.selectbox(
            "🌍 Country",
            options=available_countries,
            index=0,
            help="Filter analytics by specific country or view global total."
        )

        # Year Filter
        selected_years = st.multiselect(
            "📅 Year",
            options=available_years,
            default=available_years,
            help="Select one or multiple years."
        )

        # Month Filter
        month_names = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }
        selected_months = st.multiselect(
            "🗓️ Month",
            options=available_months,
            default=available_months,
            format_func=lambda m: f"{month_names.get(m, m)} ({m})",
            help="Select specific calendar months."
        )

        # Reset button
        if st.button("🔄 Reset Filters", use_container_width=True):
            st.rerun()

        st.markdown("<hr style='border: 0; height: 1px; background: rgba(255,255,255,0.1); margin: 20px 0;' />", unsafe_allow_html=True)

        # Pipeline Mini Status Indicator
        p_status = metadata.get("status", "SUCCESS").upper()
        status_color = "#34d399" if p_status in ["SUCCESS", "SUCCESSFUL"] else "#f87171"
        st.markdown(
            f"""
            <div style="background: rgba(30, 41, 59, 0.6); padding: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08); font-size: 0.8rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="color: #94a3b8; font-weight: 600;">Data Warehouse</span>
                    <span style="color: {status_color}; font-weight: 700;">● Online</span>
                </div>
                <div style="color: #64748b; font-size: 0.75rem;">Source: Gold Layer & DW</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        return {
            "country": selected_country,
            "years": selected_years,
            "months": selected_months
        }
