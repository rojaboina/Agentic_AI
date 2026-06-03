"""Nutrition calculations module."""
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd


def calculate_daily_totals(food_logs: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate daily totals from food logs."""
    totals = {
        'calories': 0.0,
        'protein': 0.0,
        'carbs': 0.0,
        'fats': 0.0,
        'fiber': 0.0
    }
    
    for log in food_logs:
        totals['calories'] += log['calories']
        totals['protein'] += log['protein']
        totals['carbs'] += log['carbs']
        totals['fats'] += log['fats']
        totals['fiber'] += log['fiber']
    
    return totals


def calculate_remaining(totals: Dict[str, float], goals: Dict[str, float]) -> Dict[str, float]:
    """Calculate remaining calories/macros for the day."""
    remaining = {
        'calories': goals['calorie_goal'] - totals['calories'],
        'protein': goals['protein_goal'] - totals['protein'],
        'carbs': goals['carbs_goal'] - totals['carbs'],
        'fats': goals['fats_goal'] - totals['fats']
    }
    return remaining


def calculate_percentages(totals: Dict[str, float], goals: Dict[str, float]) -> Dict[str, float]:
    """Calculate consumption percentages."""
    percentages = {
        'calories': (totals['calories'] / goals['calorie_goal'] * 100) if goals['calorie_goal'] > 0 else 0,
        'protein': (totals['protein'] / goals['protein_goal'] * 100) if goals['protein_goal'] > 0 else 0,
        'carbs': (totals['carbs'] / goals['carbs_goal'] * 100) if goals['carbs_goal'] > 0 else 0,
        'fats': (totals['fats'] / goals['fats_goal'] * 100) if goals['fats_goal'] > 0 else 0
    }
    return percentages


def calculate_macro_breakdown_percentages(totals: Dict[str, float]) -> Dict[str, float]:
    """Calculate macro breakdown as percentage of calories."""
    total_cals = totals['calories']
    if total_cals == 0:
        return {'protein_pct': 0, 'carbs_pct': 0, 'fats_pct': 0}
    
    protein_cals = totals['protein'] * 4  # 4 calories per gram
    carbs_cals = totals['carbs'] * 4      # 4 calories per gram
    fats_cals = totals['fats'] * 9        # 9 calories per gram
    
    return {
        'protein_pct': (protein_cals / total_cals * 100),
        'carbs_pct': (carbs_cals / total_cals * 100),
        'fats_pct': (fats_cals / total_cals * 100)
    }


def get_meal_breakdown(food_logs: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Get calorie and macro breakdown by meal type."""
    meals = {
        'Breakfast': {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0, 'count': 0},
        'Lunch': {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0, 'count': 0},
        'Dinner': {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0, 'count': 0},
        'Snack': {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0, 'count': 0}
    }
    
    for log in food_logs:
        meal_type = log.get('meal_type', 'Snack')
        if meal_type in meals:
            meals[meal_type]['calories'] += log['calories']
            meals[meal_type]['protein'] += log['protein']
            meals[meal_type]['carbs'] += log['carbs']
            meals[meal_type]['fats'] += log['fats']
            meals[meal_type]['count'] += 1
    
    return meals


def calculate_weekly_averages(food_logs_range: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate weekly averages."""
    if not food_logs_range:
        return {
            'avg_calories': 0,
            'avg_protein': 0,
            'avg_carbs': 0,
            'avg_fats': 0
        }
    
    # Group by date
    daily_totals = {}
    for log in food_logs_range:
        date = log['logged_date']
        if date not in daily_totals:
            daily_totals[date] = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fats': 0
            }
        daily_totals[date]['calories'] += log['calories']
        daily_totals[date]['protein'] += log['protein']
        daily_totals[date]['carbs'] += log['carbs']
        daily_totals[date]['fats'] += log['fats']
    
    days_count = len(daily_totals)
    if days_count == 0:
        return {
            'avg_calories': 0,
            'avg_protein': 0,
            'avg_carbs': 0,
            'avg_fats': 0
        }
    
    total_cals = sum(d['calories'] for d in daily_totals.values())
    total_protein = sum(d['protein'] for d in daily_totals.values())
    total_carbs = sum(d['carbs'] for d in daily_totals.values())
    total_fats = sum(d['fats'] for d in daily_totals.values())
    
    return {
        'avg_calories': total_cals / days_count,
        'avg_protein': total_protein / days_count,
        'avg_carbs': total_carbs / days_count,
        'avg_fats': total_fats / days_count
    }


def get_most_logged_foods(food_logs_range: List[Dict[str, Any]], limit: int = 5) -> List[Tuple[str, int]]:
    """Get most frequently logged foods."""
    food_counts = {}
    for log in food_logs_range:
        food_name = log['food_name']
        food_counts[food_name] = food_counts.get(food_name, 0) + 1
    
    return sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:limit]


def get_daily_data_for_chart(food_logs_range: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """Prepare daily data for charts."""
    daily_data = {}
    for log in food_logs_range:
        date = log['logged_date']
        if date not in daily_data:
            daily_data[date] = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fats': 0
            }
        daily_data[date]['calories'] += log['calories']
        daily_data[date]['protein'] += log['protein']
        daily_data[date]['carbs'] += log['carbs']
        daily_data[date]['fats'] += log['fats']
    
    # Sort by date
    sorted_data = dict(sorted(daily_data.items()))
    return sorted_data


def get_color_status(current: float, goal: float) -> str:
    """Determine color status based on consumption percentage."""
    percentage = (current / goal * 100) if goal > 0 else 0
    
    if percentage >= 95 and percentage <= 105:
        return "green"
    elif percentage >= 80 and percentage < 95:
        return "yellow"
    elif percentage > 105 and percentage <= 120:
        return "yellow"
    else:
        return "red"


def calculate_deficit_surplus(total_calories: float, goal_calories: float) -> Dict[str, Any]:
    """Calculate calorie deficit or surplus."""
    difference = total_calories - goal_calories
    return {
        'difference': difference,
        'status': 'surplus' if difference > 0 else 'deficit',
        'abs_difference': abs(difference)
    }
