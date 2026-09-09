"""
Styling & Dark Theme Component for RetailSense-AI Streamlit Dashboard.
Provides CSS injection for modern BI aesthetic, glassmorphism cards, and responsive layout elements.
"""

import streamlit as st


def apply_custom_styles():
    """
    Injects custom CSS to turn Streamlit into a state-of-the-art BI Dashboard with dark theme aesthetics.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global theme overrides */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
        }
        
        .main {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            background-attachment: fixed;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #f8fafc !important;
        }

        /* Glassmorphic KPI Cards */
        .kpi-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 20px 24px;
            margin-bottom: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        
        .kpi-card:hover {
            transform: translateY(-4px);
            border-color: rgba(99, 102, 241, 0.5);
            box-shadow: 0 20px 30px -10px rgba(99, 102, 241, 0.25);
        }

        .kpi-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.875rem;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }

        .kpi-card-value {
            font-size: 1.875rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.02em;
            margin-bottom: 4px;
        }

        .kpi-card-sub {
            font-size: 0.8rem;
            color: #64748b;
        }

        .kpi-card-icon {
            font-size: 1.5rem;
            padding: 8px;
            border-radius: 12px;
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
        }

        /* Status Badge Indicators */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .status-badge-success {
            background-color: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .status-badge-warning {
            background-color: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .status-badge-danger {
            background-color: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }

        .pulse-dot-green {
            background-color: #34d399;
            box-shadow: 0 0 10px #34d399;
        }

        .pulse-dot-red {
            background-color: #f87171;
            box-shadow: 0 0 10px #f87171;
        }

        /* Button Styling */
        .stButton button, .stDownloadButton button {
            background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 8px 16px !important;
            transition: all 0.2s ease-in-out !important;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important;
        }

        .stButton button:hover, .stDownloadButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #0f172a;
        }
        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #475569;
        }
        
        /* Metric header text */
        .page-title {
            font-size: 2.25rem;
            font-weight: 800;
            background: linear-gradient(90deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.25rem;
        }
        
        .page-subtitle {
            color: #94a3b8;
            font-size: 1.05rem;
            margin-bottom: 1.75rem;
        }

        /* Header Accent Line */
        .accent-line {
            height: 3px;
            width: 80px;
            background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
            border-radius: 2px;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
