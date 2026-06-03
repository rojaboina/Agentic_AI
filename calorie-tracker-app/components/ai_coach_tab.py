"""AI Nutrition Coach chat tab component."""
import streamlit as st
from datetime import datetime, timedelta
from utils import database, nutrition_calc, llm_agent, data_processing
from typing import Dict, Any, List


def render_ai_coach_tab(goals: Dict[str, Any]) -> None:
    """Render AI Nutrition Coach tab."""
    st.header("🤖 AI Nutrition Coach")
    
    st.markdown("""
    Welcome to your AI Nutrition Coach! Ask questions about your nutrition, meal plans, 
    macro balance, and more. The coach has access to your nutrition data from the past week.
    
    **Note:** The advice is for educational purposes only and not a substitute for professional medical advice.
    """)
    
    # Initialize coach
    coach = llm_agent.NutritionCoach()
    
    if not coach.is_available():
        st.error(f"❌ AI Coach unavailable: {coach.get_error_message()}")
        st.info("Please set your GROQ_API_KEY environment variable to enable AI features.")
        return
    
    # Get nutrition context
    today = datetime.now().strftime('%Y-%m-%d')
    start_date, _ = data_processing.get_date_range(days_back=7)
    
    # Today's data
    today_logs = database.get_food_logs(today)
    today_totals = nutrition_calc.calculate_daily_totals(today_logs)
    today_remaining = nutrition_calc.calculate_remaining(today_totals, goals)
    today_meal_breakdown = nutrition_calc.get_meal_breakdown(today_logs)
    
    # Weekly data
    weekly_logs = database.get_food_logs_range(start_date, today)
    weekly_avg = nutrition_calc.calculate_weekly_averages(weekly_logs)
    most_logged = nutrition_calc.get_most_logged_foods(weekly_logs, limit=5)
    
    # Prepare context for AI
    nutrition_context = {
        'daily_totals': today_totals,
        'goals': goals,
        'remaining': today_remaining,
        'most_logged_foods': most_logged,
        'meal_breakdown': today_meal_breakdown,
        'weekly_averages': weekly_avg
    }
    
    # Initialize session state for chat
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat messages
    chat_container = st.container(height=400, border=True)
    
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.chat_message("user").write(message['content'])
            else:
                st.chat_message("assistant").write(message['content'])
    
    # Chat input
    st.markdown("---")
    
    user_input = st.chat_input(
        "Ask me anything about your nutrition!",
        key="coach_input"
    )
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Display user message
        with chat_container:
            st.chat_message("user").write(user_input)
        
        # Get AI response
        with st.spinner("🤖 Coach is thinking..."):
            ai_response = coach.chat(user_input, nutrition_context)
        
        # Add AI response to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': ai_response
        })
        
        # Display AI response
        with chat_container:
            st.chat_message("assistant").write(ai_response)
        
        st.rerun()
    
    # Example prompts
    st.markdown("---")
    st.markdown("### 💡 Example Questions")
    
    example_prompts = [
        "What should I eat for lunch to hit my protein goal?",
        "Am I eating too many carbs today?",
        "What foods have I logged the most this week?",
        "How's my macro balance today?",
        "Give me suggestions to improve my nutrition",
        "Why am I consistently under my protein goal?"
    ]
    
    cols = st.columns(2)
    for i, prompt in enumerate(example_prompts):
        with cols[i % 2]:
            if st.button(prompt, use_container_width=True):
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': prompt
                })
                
                with st.spinner("🤖 Coach is thinking..."):
                    ai_response = coach.chat(prompt, nutrition_context)
                
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': ai_response
                })
                
                st.rerun()
    
    # Clear chat button
    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
