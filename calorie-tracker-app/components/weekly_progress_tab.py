"""Weekly Progress tab component."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from utils import database, nutrition_calc, data_processing
from typing import Dict, Any


def render_weekly_progress_tab(goals: Dict[str, Any]) -> None:
    """Render Weekly Progress tab."""
    st.header("📈 Weekly Progress")
    
    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get food logs for the week
    food_logs = database.get_food_logs_range(start_date_str, end_date_str)
    
    if not food_logs:
        st.info("No data available for the past week. Start logging your meals!")
        return
    
    # Get daily data
    daily_data = nutrition_calc.get_daily_data_for_chart(food_logs)
    
    # Summary statistics
    st.markdown("### 📊 Weekly Statistics")
    
    weekly_avg = nutrition_calc.calculate_weekly_averages(food_logs)
    most_logged = nutrition_calc.get_most_logged_foods(food_logs, limit=5)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Daily Calories", f"{weekly_avg['avg_calories']:.0f}")
    with col2:
        st.metric("Avg Daily Protein", f"{weekly_avg['avg_protein']:.0f}g")
    with col3:
        st.metric("Avg Daily Carbs", f"{weekly_avg['avg_carbs']:.0f}g")
    with col4:
        st.metric("Avg Daily Fats", f"{weekly_avg['avg_fats']:.0f}g")
    
    st.markdown("---")
    
    # Charts
    st.markdown("### 📊 Trends")
    
    col1, col2 = st.columns(2)
    
    # Calorie trend line chart
    with col1:
        dates = list(daily_data.keys())
        calories = [daily_data[d]['calories'] for d in dates]
        
        fig_cal = go.Figure()
        fig_cal.add_trace(go.Scatter(
            x=dates,
            y=calories,
            mode='lines+markers',
            name='Calories',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=8)
        ))
        fig_cal.add_hline(y=goals['calorie_goal'], line_dash="dash", line_color="green", 
                         annotation_text="Goal", annotation_position="right")
        fig_cal.update_layout(
            title="Daily Calorie Trend",
            xaxis_title="Date",
            yaxis_title="Calories",
            height=350,
            hovermode='x unified'
        )
        st.plotly_chart(fig_cal, use_container_width=True)
    
    # Macro stacked bar chart
    with col2:
        dates = list(daily_data.keys())
        proteins = [daily_data[d]['protein'] for d in dates]
        carbs = [daily_data[d]['carbs'] for d in dates]
        fats = [daily_data[d]['fats'] for d in dates]
        
        fig_macro = go.Figure()
        fig_macro.add_trace(go.Bar(x=dates, y=proteins, name='Protein', marker_color='#4ECDC4'))
        fig_macro.add_trace(go.Bar(x=dates, y=carbs, name='Carbs', marker_color='#FFE66D'))
        fig_macro.add_trace(go.Bar(x=dates, y=fats, name='Fats', marker_color='#FF6B6B'))
        
        fig_macro.update_layout(
            barmode='stack',
            title="Daily Macro Breakdown",
            xaxis_title="Date",
            yaxis_title="Grams",
            height=350,
            hovermode='x'
        )
        st.plotly_chart(fig_macro, use_container_width=True)
    
    # Most logged foods
    st.markdown("---")
    st.markdown("### 🥇 Most Logged Foods")
    
    if most_logged:
        for i, (food_name, count) in enumerate(most_logged, 1):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{i}. **{food_name}**")
            with col2:
                st.write(f"**{count}x** logged")
    else:
        st.info("No foods logged this week.")
    
    # Daily table view
    st.markdown("---")
    st.markdown("### 📋 Daily Breakdown")
    
    # Create DataFrame
    daily_df_data = []
    for date, data in daily_data.items():
        daily_df_data.append({
            'Date': date,
            'Calories': f"{data['calories']:.0f}",
            'Protein (g)': f"{data['protein']:.0f}",
            'Carbs (g)': f"{data['carbs']:.0f}",
            'Fats (g)': f"{data['fats']:.0f}"
        })
    
    if daily_df_data:
        df = pd.DataFrame(daily_df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
