"""
AI-Powered Calorie & Macro Tracker App
A production-quality nutrition tracking application with AI-powered insights.
"""

import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import utilities and components
from utils import database
from components import (
    settings_sidebar,
    daily_log_tab,
    today_summary_tab,
    weekly_progress_tab,
    nutrition_search_tab,
    ai_coach_tab
)

# Page configuration
st.set_page_config(
    page_title="🥗 Calorie Tracker",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
    <style>
    /* Global Styles */
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Main Container */
    .main {
        padding: 2rem 1rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Header */
    h1 {
        color: #2d3748;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        background-color: #e2e8f0;
        border-radius: 8px;
        color: #4a5568;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e2e8f0 !important;
        padding: 0.75rem !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Progress Bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize database
database.init_db()

# Initialize session state
if 'selected_food' not in st.session_state:
    st.session_state.selected_food = None

# App title
st.title("🥗 Calorie & Macro Tracker")
st.markdown("Your personal AI-powered nutrition companion")

# Render settings sidebar and get user goals
user_goals = settings_sidebar.render_settings_sidebar()

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Daily Log",
    "📊 Today's Summary",
    "📈 Weekly Progress",
    "🔍 Food Database",
    "🤖 AI Coach"
])

with tab1:
    daily_log_tab.render_daily_log_tab()

with tab2:
    today_summary_tab.render_today_summary_tab(user_goals)

with tab3:
    weekly_progress_tab.render_weekly_progress_tab(user_goals)

with tab4:
    nutrition_search_tab.render_nutrition_search_tab()

with tab5:
    ai_coach_tab.render_ai_coach_tab(user_goals)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.8rem; margin-top: 2rem;'>
    <p>💡 <strong>Disclaimer:</strong> This app is for educational and informational purposes only. 
    The AI coach is not a doctor or registered dietitian. Always consult with healthcare professionals 
    before making significant dietary changes.</p>
    <p>Built with ❤️ using Streamlit, Groq, and LangChain</p>
</div>
""", unsafe_allow_html=True)
