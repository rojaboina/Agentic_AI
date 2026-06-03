"""Food database search functionality."""
import requests
import json
from typing import List, Dict, Any
from pathlib import Path


# Sample local food database
SAMPLE_FOODS = [
    {'name': 'Chicken Breast', 'serving_size': 100, 'unit': 'g', 'calories': 165, 'protein': 31, 'carbs': 0, 'fats': 3.6, 'fiber': 0, 'sodium': 74},
    {'name': 'Broccoli', 'serving_size': 100, 'unit': 'g', 'calories': 34, 'protein': 2.8, 'carbs': 7, 'fats': 0.4, 'fiber': 2.4, 'sodium': 64},
    {'name': 'Brown Rice', 'serving_size': 100, 'unit': 'g', 'calories': 111, 'protein': 2.6, 'carbs': 23, 'fats': 0.9, 'fiber': 1.8, 'sodium': 7},
    {'name': 'Salmon', 'serving_size': 100, 'unit': 'g', 'calories': 208, 'protein': 20, 'carbs': 0, 'fats': 13, 'fiber': 0, 'sodium': 59},
    {'name': 'Almonds', 'serving_size': 28, 'unit': 'g', 'calories': 164, 'protein': 6, 'carbs': 6, 'fats': 14, 'fiber': 3.5, 'sodium': 0},
    {'name': 'Banana', 'serving_size': 118, 'unit': 'g', 'calories': 105, 'protein': 1.3, 'carbs': 27, 'fats': 0.3, 'fiber': 3.1, 'sodium': 2},
    {'name': 'Greek Yogurt', 'serving_size': 100, 'unit': 'g', 'calories': 59, 'protein': 10.2, 'carbs': 3.3, 'fats': 0.4, 'fiber': 0, 'sodium': 75},
    {'name': 'Egg', 'serving_size': 50, 'unit': 'g', 'calories': 78, 'protein': 6.3, 'carbs': 0.6, 'fats': 5.3, 'fiber': 0, 'sodium': 72},
    {'name': 'Oatmeal', 'serving_size': 40, 'unit': 'g', 'calories': 150, 'protein': 5, 'carbs': 27, 'fats': 3, 'fiber': 4, 'sodium': 2},
    {'name': 'Spinach', 'serving_size': 100, 'unit': 'g', 'calories': 23, 'protein': 2.7, 'carbs': 3.6, 'fats': 0.4, 'fiber': 2.2, 'sodium': 71},
    {'name': 'Sweet Potato', 'serving_size': 100, 'unit': 'g', 'calories': 86, 'protein': 1.6, 'carbs': 20, 'fats': 0.1, 'fiber': 3, 'sodium': 55},
    {'name': 'Beef Lean', 'serving_size': 100, 'unit': 'g', 'calories': 180, 'protein': 26, 'carbs': 0, 'fats': 8, 'fiber': 0, 'sodium': 75},
    {'name': 'Avocado', 'serving_size': 100, 'unit': 'g', 'calories': 160, 'protein': 2, 'carbs': 9, 'fats': 15, 'fiber': 7, 'sodium': 7},
    {'name': 'Blueberries', 'serving_size': 100, 'unit': 'g', 'calories': 57, 'protein': 0.7, 'carbs': 14, 'fats': 0.3, 'fiber': 2.4, 'sodium': 1},
    {'name': 'White Rice', 'serving_size': 100, 'unit': 'g', 'calories': 130, 'protein': 2.7, 'carbs': 28, 'fats': 0.3, 'fiber': 0.4, 'sodium': 2},
    {'name': 'Whole Wheat Bread', 'serving_size': 28, 'unit': 'g', 'calories': 80, 'protein': 4, 'carbs': 14, 'fats': 1, 'fiber': 2, 'sodium': 140},
    {'name': 'Peanut Butter', 'serving_size': 32, 'unit': 'g', 'calories': 188, 'protein': 8, 'carbs': 7, 'fats': 16, 'fiber': 1.5, 'sodium': 150},
    {'name': 'Milk', 'serving_size': 240, 'unit': 'ml', 'calories': 149, 'protein': 7.7, 'carbs': 11.7, 'fats': 7.7, 'fiber': 0, 'sodium': 107},
    {'name': 'Cottage Cheese', 'serving_size': 100, 'unit': 'g', 'calories': 98, 'protein': 11, 'carbs': 3.4, 'fats': 5, 'fiber': 0, 'sodium': 364},
    {'name': 'Tuna', 'serving_size': 100, 'unit': 'g', 'calories': 132, 'protein': 29, 'carbs': 0, 'fats': 1.3, 'fiber': 0, 'sodium': 41},
]


def search_foods(query: str) -> List[Dict[str, Any]]:
    """
    Search for foods in local database.
    In production, this could integrate with USDA FoodData Central API.
    """
    query_lower = query.lower().strip()
    
    if not query_lower:
        return []
    
    results = []
    for food in SAMPLE_FOODS:
        if query_lower in food['name'].lower():
            results.append({
                'name': food['name'],
                'serving_size': food['serving_size'],
                'unit': food['unit'],
                'calories': food['calories'],
                'protein': food['protein'],
                'carbs': food['carbs'],
                'fats': food['fats'],
                'fiber': food['fiber'],
                'sodium': food['sodium']
            })
    
    return results


def get_food_by_name(food_name: str) -> Dict[str, Any] | None:
    """Get food details by exact name."""
    for food in SAMPLE_FOODS:
        if food['name'].lower() == food_name.lower():
            return food
    return None


def get_all_foods() -> List[Dict[str, Any]]:
    """Get all available foods from database."""
    return SAMPLE_FOODS


def calculate_nutrition_for_portion(food: Dict[str, Any], portion_size: float) -> Dict[str, float]:
    """
    Calculate nutrition values for a custom portion size.
    Standard serving size is stored in food['serving_size']
    """
    if food['serving_size'] == 0:
        return food.copy()
    
    multiplier = portion_size / food['serving_size']
    
    return {
        'calories': food['calories'] * multiplier,
        'protein': food['protein'] * multiplier,
        'carbs': food['carbs'] * multiplier,
        'fats': food['fats'] * multiplier,
        'fiber': food['fiber'] * multiplier,
        'sodium': food['sodium'] * multiplier
    }
