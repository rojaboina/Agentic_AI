"""Settings sidebar component."""
import streamlit as st
from utils import database
from typing import Dict, Any


def render_settings_sidebar() -> Dict[str, Any]:
    """Render user settings in sidebar."""
    with st.sidebar:
        # Enhanced sidebar header
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem 0; color: white;'>
            <h2 style='margin: 0; font-size: 1.8rem;'>⚙️ Settings</h2>
            <p style='margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;'>Customize your goals</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Get current settings
        settings = database.get_user_settings()
        
        # Daily Goals Section
        st.markdown("### 📊 Daily Goals")
        
        col1, col2 = st.columns(2)
        with col1:
            calorie_goal = st.number_input(
                "Calorie Goal",
                value=settings.get('calorie_goal', 2000),
                step=100,
                min_value=1000,
                max_value=5000
            )
        with col2:
            protein_goal = st.number_input(
                "Protein Goal (g)",
                value=settings.get('protein_goal', 150),
                step=10,
                min_value=50,
                max_value=300
            )
        
        col1, col2 = st.columns(2)
        with col1:
            carbs_goal = st.number_input(
                "Carbs Goal (g)",
                value=settings.get('carbs_goal', 225),
                step=10,
                min_value=50,
                max_value=500
            )
        with col2:
            fats_goal = st.number_input(
                "Fats Goal (g)",
                value=settings.get('fats_goal', 65),
                step=5,
                min_value=20,
                max_value=200
            )
        
        # Water & Other
        st.markdown("### 💧 Other Targets")
        
        water_goal = st.number_input(
            "Daily Water Goal (oz)",
            value=settings.get('water_goal_oz', 64),
            step=8,
            min_value=32,
            max_value=128
        )
        
        # Preferences
        st.markdown("### 🍽️ Preferences")
        
        col1, col2 = st.columns(2)
        with col1:
            dietary_pref = st.selectbox(
                "Dietary Preference",
                ["None", "Vegan", "Vegetarian", "Keto"],
                index=["None", "Vegan", "Vegetarian", "Keto"].index(
                    settings.get('dietary_preference', 'None')
                )
            )
        
        with col2:
            activity_level = st.selectbox(
                "Activity Level",
                ["sedentary", "light", "moderate", "active", "very_active"],
                index=["sedentary", "light", "moderate", "active", "very_active"].index(
                    settings.get('activity_level', 'moderate')
                )
            )
        
        # Save Settings Button
        if st.button("💾 Save Settings", use_container_width=True):
            new_settings = {
                'calorie_goal': calorie_goal,
                'protein_goal': protein_goal,
                'carbs_goal': carbs_goal,
                'fats_goal': fats_goal,
                'water_goal_oz': water_goal,
                'dietary_preference': dietary_pref,
                'activity_level': activity_level
            }
            database.update_user_settings(new_settings)
            st.success("✅ Settings saved!")
            st.rerun()
        
        st.markdown("---")
        
        return {
            'calorie_goal': calorie_goal,
            'protein_goal': protein_goal,
            'carbs_goal': carbs_goal,
            'fats_goal': fats_goal,
            'water_goal_oz': water_goal,
            'dietary_preference': dietary_pref,
            'activity_level': activity_level
        }
