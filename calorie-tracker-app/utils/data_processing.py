"""Data processing utilities."""
from datetime import datetime
from typing import Dict, Any, List


def validate_food_input(food_name: str, portion_size: float, meal_type: str) -> tuple[bool, str]:
    """Validate food input parameters."""
    if not food_name or not food_name.strip():
        return False, "Food name cannot be empty"
    
    if portion_size <= 0:
        return False, "Portion size must be greater than 0"
    
    valid_meals = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
    if meal_type not in valid_meals:
        return False, f"Meal type must be one of {valid_meals}"
    
    return True, "Valid"


def format_nutrition_value(value: float, decimals: int = 1) -> str:
    """Format nutrition value for display."""
    return f"{value:.{decimals}f}"


def format_currency(value: float) -> str:
    """Format value as currency (for future use)."""
    return f"${value:.2f}"


def parse_date_string(date_str: str) -> str:
    """Parse and validate date string."""
    try:
        parsed = datetime.fromisoformat(date_str)
        return parsed.strftime('%Y-%m-%d')
    except:
        return datetime.now().strftime('%Y-%m-%d')


def normalize_food_name(name: str) -> str:
    """Normalize food name for consistency."""
    return name.strip().title()


def get_date_range(days_back: int = 7) -> tuple[str, str]:
    """Get date range for last N days."""
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back - 1)
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
