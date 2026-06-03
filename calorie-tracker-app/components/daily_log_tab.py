"""Daily Food Log tab component."""
import streamlit as st
from datetime import datetime
from utils import database, food_search, data_processing, nutrition_calc
from typing import Dict, Any, List


def render_daily_log_tab() -> None:
    """Render the Daily Food Log tab."""
    st.header("📝 Daily Food Log")
    
    # Date picker
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        selected_date = st.date_input(
            "Select Date",
            value=datetime.now(),
            key="daily_log_date"
        )
    
    selected_date_str = selected_date.strftime('%Y-%m-%d')
    
    # Food search and add section
    st.markdown("### 🔍 Add Food")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "Search for food",
            placeholder="e.g., Chicken Breast, Broccoli...",
            key="food_search"
        )
    
    search_results = []
    selected_food = None
    
    if search_query:
        search_results = food_search.search_foods(search_query)
        
        if search_results:
            st.markdown("**Search Results:**")
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 0.5])
            
            with col1:
                st.markdown("**Food Name**")
            with col2:
                st.markdown("**Serving**")
            with col3:
                st.markdown("**Calories**")
            with col4:
                st.markdown("**Protein (g)**")
            with col5:
                st.markdown("**Select**")
            
            for i, food in enumerate(search_results):
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 0.5])
                
                with col1:
                    st.markdown(f"{food['name']}")
                with col2:
                    st.markdown(f"{food['serving_size']}{food['unit']}")
                with col3:
                    st.markdown(f"{food['calories']:.0f}")
                with col4:
                    st.markdown(f"{food['protein']:.0f}")
                with col5:
                    if st.button("✓", key=f"select_food_{i}"):
                        st.session_state.selected_food = food
                        st.rerun()
        else:
            st.info("No foods found. Try a different search term.")
    
    # If food is selected, show portion input
    if 'selected_food' in st.session_state and st.session_state.selected_food:
        selected_food = st.session_state.selected_food
        st.success(f"✓ Selected: **{selected_food['name']}**")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            portion_size = st.number_input(
                "Portion Size",
                value=float(selected_food['serving_size']),
                step=10.0,
                min_value=1.0,
                key="portion_size"
            )
        
        with col2:
            meal_type = st.selectbox(
                "Meal Type",
                ["Breakfast", "Lunch", "Dinner", "Snack"],
                key="meal_type"
            )
        
        with col3:
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            add_button = st.button("➕ Add Food", use_container_width=True)
        
        if add_button:
            # Validate input
            is_valid, message = data_processing.validate_food_input(
                selected_food['name'],
                portion_size,
                meal_type
            )
            
            if is_valid:
                # Calculate nutrition for portion
                nutrition = food_search.calculate_nutrition_for_portion(selected_food, portion_size)
                
                # Log to database
                database.log_food(
                    food_name=selected_food['name'],
                    portion_size=portion_size,
                    unit=selected_food['unit'],
                    calories=nutrition['calories'],
                    protein=nutrition['protein'],
                    carbs=nutrition['carbs'],
                    fats=nutrition['fats'],
                    fiber=nutrition['fiber'],
                    meal_type=meal_type,
                    logged_date=selected_date_str
                )
                
                st.success(f"✅ Added {selected_food['name']} to {meal_type}!")
                
                # Clear selection
                del st.session_state.selected_food
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    # Display logged foods for the day
    st.markdown("---")
    st.markdown("### 📋 Today's Logged Foods")
    
    food_logs = database.get_food_logs(selected_date_str)
    
    if food_logs:
        # Create table header
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1, 1, 1, 1, 1, 1, 0.5])
        
        with col1:
            st.markdown("**Food**")
        with col2:
            st.markdown("**Meal**")
        with col3:
            st.markdown("**Portion**")
        with col4:
            st.markdown("**Cal**")
        with col5:
            st.markdown("**P (g)**")
        with col6:
            st.markdown("**C (g)**")
        with col7:
            st.markdown("**F (g)**")
        with col8:
            st.markdown("**Delete**")
        
        for log in food_logs:
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1, 1, 1, 1, 1, 1, 0.5])
            
            with col1:
                st.markdown(f"{log['food_name']}")
            with col2:
                st.markdown(f"{log['meal_type']}")
            with col3:
                st.markdown(f"{log['portion_size']:.0f}{log['unit']}")
            with col4:
                st.markdown(f"{log['calories']:.0f}")
            with col5:
                st.markdown(f"{log['protein']:.1f}")
            with col6:
                st.markdown(f"{log['carbs']:.1f}")
            with col7:
                st.markdown(f"{log['fats']:.1f}")
            with col8:
                if st.button("🗑️", key=f"delete_{log['id']}"):
                    database.delete_food_log(log['id'])
                    st.success("Deleted!")
                    st.rerun()
        
        # Show totals
        st.markdown("---")
        totals = nutrition_calc.calculate_daily_totals(food_logs)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Calories", f"{totals['calories']:.0f}")
        with col2:
            st.metric("Total Protein", f"{totals['protein']:.1f}g")
        with col3:
            st.metric("Total Carbs", f"{totals['carbs']:.1f}g")
        with col4:
            st.metric("Total Fats", f"{totals['fats']:.1f}g")
        with col5:
            st.metric("Total Fiber", f"{totals['fiber']:.1f}g")
    
    else:
        st.info("No foods logged for this day yet. Add your first food above!")
