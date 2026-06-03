"""Today's Summary tab component."""
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from utils import database, nutrition_calc, llm_agent
from typing import Dict, Any


def render_today_summary_tab(goals: Dict[str, Any]) -> None:
    """Render Today's Summary tab."""
    st.header("📊 Today's Summary")
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get food logs for today
    food_logs = database.get_food_logs(today)
    
    # Calculate totals
    totals = nutrition_calc.calculate_daily_totals(food_logs)
    remaining = nutrition_calc.calculate_remaining(totals, goals)
    percentages = nutrition_calc.calculate_percentages(totals, goals)
    
    # Macro breakdown percentages
    macro_pct = nutrition_calc.calculate_macro_breakdown_percentages(totals)
    
    # Display metric cards with modern styling
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; color: white; margin-bottom: 1.5rem;'>
        <h3 style='margin: 0; color: white;'>Your Daily Progress</h3>
        <p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>Stay on track with your nutrition goals</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    with col1:
        cal_status = nutrition_calc.get_color_status(totals['calories'], goals['calorie_goal'])
        st.markdown(f"""
        <div style='background: white; padding: 1.5rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); border-left: 4px solid #667eea;'>
            <p style='margin: 0; color: #888; font-size: 0.9rem; font-weight: 500;'>CALORIES</p>
            <h2 style='margin: 0.5rem 0; color: #2d3748;'>{totals['calories']:.0f}</h2>
            <p style='margin: 0.5rem 0 0 0; color: #667eea; font-weight: 600;'>{remaining['calories']:.0f} remaining</p>
            <div style='background: #e2e8f0; height: 6px; border-radius: 3px; margin-top: 0.75rem; overflow: hidden;'>
                <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); width: {percentages["calories"]*100}%; height: 100%;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='background: white; padding: 1.5rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); border-left: 4px solid #f093fb;'>
            <p style='margin: 0; color: #888; font-size: 0.9rem; font-weight: 500;'>PROTEIN</p>
            <h2 style='margin: 0.5rem 0; color: #2d3748;'>{totals['protein']:.0f}g</h2>
            <p style='margin: 0.5rem 0 0 0; color: #f093fb; font-weight: 600;'>{remaining['protein']:.0f}g left</p>
            <div style='background: #e2e8f0; height: 6px; border-radius: 3px; margin-top: 0.75rem; overflow: hidden;'>
                <div style='background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%); width: {percentages["protein"]*100}%; height: 100%;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style='background: white; padding: 1.5rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); border-left: 4px solid #fa709a;'>
            <p style='margin: 0; color: #888; font-size: 0.9rem; font-weight: 500;'>CARBS</p>
            <h2 style='margin: 0.5rem 0; color: #2d3748;'>{totals['carbs']:.0f}g</h2>
            <p style='margin: 0.5rem 0 0 0; color: #fa709a; font-weight: 600;'>{remaining['carbs']:.0f}g left</p>
            <div style='background: #e2e8f0; height: 6px; border-radius: 3px; margin-top: 0.75rem; overflow: hidden;'>
                <div style='background: linear-gradient(90deg, #fa709a 0%, #fee140 100%); width: {percentages["carbs"]*100}%; height: 100%;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style='background: white; padding: 1.5rem; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); border-left: 4px solid #4facfe;'>
            <p style='margin: 0; color: #888; font-size: 0.9rem; font-weight: 500;'>FATS</p>
            <h2 style='margin: 0.5rem 0; color: #2d3748;'>{totals['fats']:.0f}g</h2>
            <p style='margin: 0.5rem 0 0 0; color: #4facfe; font-weight: 600;'>{remaining['fats']:.0f}g left</p>
            <div style='background: #e2e8f0; height: 6px; border-radius: 3px; margin-top: 0.75rem; overflow: hidden;'>
                <div style='background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); width: {percentages["fats"]*100}%; height: 100%;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        carbs_status = nutrition_calc.get_color_status(totals['carbs'], goals['carbs_goal'])
        st.metric(
            "Carbs",
            f"{totals['carbs']:.0f}g",
            f"{remaining['carbs']:.0f}g left",
            delta_color="inverse"
        )
    
    with col4:
        fats_status = nutrition_calc.get_color_status(totals['fats'], goals['fats_goal'])
        st.metric(
            "Fats",
            f"{totals['fats']:.0f}g",
            f"{remaining['fats']:.0f}g left",
            delta_color="inverse"
        )
    
    # Charts
    st.markdown("---")
    st.markdown("### 📊 Visualizations")
    
    col1, col2 = st.columns(2)
    
    # Calorie consumption donut chart
    with col1:
        fig_cal = go.Figure(data=[go.Pie(
            labels=['Consumed', 'Remaining'],
            values=[totals['calories'], max(0, remaining['calories'])],
            hole=0.3,
            marker=dict(colors=['#FF6B6B', '#95E1D3'])
        )])
        fig_cal.update_layout(
            title="Calorie Distribution",
            height=300,
            showlegend=True
        )
        st.plotly_chart(fig_cal, use_container_width=True)
    
    # Macro breakdown pie chart
    with col2:
        fig_macro = go.Figure(data=[go.Pie(
            labels=['Protein', 'Carbs', 'Fats'],
            values=[macro_pct['protein_pct'], macro_pct['carbs_pct'], macro_pct['fats_pct']],
            marker=dict(colors=['#4ECDC4', '#FF6B6B', '#FFE66D'])
        )])
        fig_macro.update_layout(
            title="Macro Breakdown",
            height=300,
            showlegend=True
        )
        st.plotly_chart(fig_macro, use_container_width=True)
    
    # Macro target progress
    st.markdown("### 📍 Macro Progress")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.progress(
            min(percentages['protein'] / 100, 1.0),
            text=f"Protein: {percentages['protein']:.0f}%"
        )
    with col2:
        st.progress(
            min(percentages['carbs'] / 100, 1.0),
            text=f"Carbs: {percentages['carbs']:.0f}%"
        )
    with col3:
        st.progress(
            min(percentages['fats'] / 100, 1.0),
            text=f"Fats: {percentages['fats']:.0f}%"
        )
    
    # Meal breakdown
    st.markdown("---")
    st.markdown("### 🍽️ Meal Breakdown")
    
    meal_breakdown = nutrition_calc.get_meal_breakdown(food_logs)
    
    meal_cols = st.columns(4)
    meals = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
    
    for i, meal in enumerate(meals):
        with meal_cols[i]:
            data = meal_breakdown[meal]
            if data['count'] > 0:
                st.metric(
                    meal,
                    f"{data['calories']:.0f} cal",
                    f"{data['count']} item(s)"
                )
            else:
                st.metric(meal, "0 cal", "Not logged")
    
    # Water intake tracker
    st.markdown("---")
    st.markdown("### 💧 Water Intake")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        water_logged = database.get_water_intake(today)
        water_goal = goals['water_goal_oz']
        
        st.progress(
            min(water_logged / water_goal, 1.0),
            text=f"{water_logged:.0f} / {water_goal:.0f} oz"
        )
    
    with col2:
        water_amount = st.number_input("Add water (oz)", value=8.0, step=4.0, min_value=0.0)
    
    with col3:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if st.button("💧 Log Water", use_container_width=True):
            database.log_water(water_amount, today)
            st.success("Water logged!")
            st.rerun()
    
    # AI Nutrition Insight
    st.markdown("---")
    st.markdown("### 🤖 AI Nutrition Insight")
    
    coach = llm_agent.NutritionCoach()
    
    if coach.is_available():
        if st.button("🔄 Generate Insight", use_container_width=True):
            with st.spinner("Generating personalized insight..."):
                insight = coach.generate_nutrition_insight(totals, goals, meal_breakdown)
                st.info(insight)
    else:
        st.warning(f"⚠️ AI insights unavailable: {coach.get_error_message()}")
