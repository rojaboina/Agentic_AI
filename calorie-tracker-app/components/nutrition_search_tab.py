"""Nutrition Database Search tab component."""
import streamlit as st
from utils import food_search, database
from typing import List, Dict, Any


def render_nutrition_search_tab() -> None:
    """Render Nutrition Database Search tab."""
    st.header("🔍 Nutrition Database")
    
    st.markdown("### 🥘 Browse Foods")
    
    # Search and filter options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input(
            "Search foods",
            placeholder="e.g., chicken, rice, apple...",
            key="nutrition_search"
        )
    
    # Display all foods or search results
    if search_term:
        results = food_search.search_foods(search_term)
        st.markdown(f"**Found {len(results)} food(s)**")
    else:
        results = food_search.get_all_foods()
        st.markdown(f"**Showing all {len(results)} foods**")
    
    if results:
        # Table header
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1, 1, 1, 1, 1, 1, 1])
        
        with col1:
            st.markdown("**Food Name**")
        with col2:
            st.markdown("**Serving**")
        with col3:
            st.markdown("**Cal**")
        with col4:
            st.markdown("**Protein**")
        with col5:
            st.markdown("**Carbs**")
        with col6:
            st.markdown("**Fats**")
        with col7:
            st.markdown("**Fiber**")
        with col8:
            st.markdown("**Favorite**")
        
        # Display foods
        for food in results:
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1, 1, 1, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"{food['name']}")
            with col2:
                st.markdown(f"{food['serving_size']}{food['unit']}")
            with col3:
                st.markdown(f"{food['calories']:.0f}")
            with col4:
                st.markdown(f"{food['protein']:.0f}g")
            with col5:
                st.markdown(f"{food['carbs']:.0f}g")
            with col6:
                st.markdown(f"{food['fats']:.1f}g")
            with col7:
                st.markdown(f"{food['fiber']:.1f}g")
            with col8:
                if st.button("❤️", key=f"fav_{food['name']}"):
                    database.add_favorite_food(
                        food_name=food['name'],
                        portion_size=food['serving_size'],
                        unit=food['unit'],
                        calories=food['calories'],
                        protein=food['protein'],
                        carbs=food['carbs'],
                        fats=food['fats'],
                        fiber=food['fiber']
                    )
                    st.success(f"Added {food['name']} to favorites!")
                    st.rerun()
    else:
        st.info("No foods found. Try a different search term.")
    
    # Favorite foods section
    st.markdown("---")
    st.markdown("### ❤️ Favorite Foods")
    
    favorites = database.get_favorite_foods()
    
    if favorites:
        # Table header
        col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1, 1])
        
        with col1:
            st.markdown("**Food Name**")
        with col2:
            st.markdown("**Serving**")
        with col3:
            st.markdown("**Cal**")
        with col4:
            st.markdown("**Protein**")
        with col5:
            st.markdown("**Carbs**")
        with col6:
            st.markdown("**Fats**")
        with col7:
            st.markdown("**Action**")
        
        # Display favorites
        for fav in favorites:
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"{fav['food_name']}")
            with col2:
                st.markdown(f"{fav['portion_size']:.0f}{fav['unit']}")
            with col3:
                st.markdown(f"{fav['calories']:.0f}")
            with col4:
                st.markdown(f"{fav['protein']:.0f}g")
            with col5:
                st.markdown(f"{fav['carbs']:.0f}g")
            with col6:
                st.markdown(f"{fav['fats']:.1f}g")
            with col7:
                if st.button("🗑️", key=f"remove_fav_{fav['id']}"):
                    st.info("Remove favorite feature coming soon!")
    else:
        st.info("No favorite foods yet. Add some by clicking the ❤️ button!")
