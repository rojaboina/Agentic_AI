"""Database management for food logs and user settings."""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "nutrition_db.sqlite"


def init_db() -> None:
    """Initialize SQLite database with required tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # User settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY,
            calorie_goal INTEGER DEFAULT 2000,
            protein_goal INTEGER DEFAULT 150,
            carbs_goal INTEGER DEFAULT 225,
            fats_goal INTEGER DEFAULT 65,
            water_goal_oz INTEGER DEFAULT 64,
            dietary_preference TEXT DEFAULT 'None',
            activity_level TEXT DEFAULT 'moderate',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Food logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_logs (
            id INTEGER PRIMARY KEY,
            food_name TEXT NOT NULL,
            portion_size REAL NOT NULL,
            unit TEXT NOT NULL,
            calories REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fats REAL NOT NULL,
            fiber REAL NOT NULL,
            meal_type TEXT NOT NULL,
            logged_date DATE NOT NULL,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Favorite foods table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorite_foods (
            id INTEGER PRIMARY KEY,
            food_name TEXT NOT NULL,
            portion_size REAL NOT NULL,
            unit TEXT NOT NULL,
            calories REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fats REAL NOT NULL,
            fiber REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Water intake table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_intake (
            id INTEGER PRIMARY KEY,
            amount_oz REAL NOT NULL,
            logged_date DATE NOT NULL,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Weight tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weight_tracking (
            id INTEGER PRIMARY KEY,
            weight_lbs REAL NOT NULL,
            logged_date DATE NOT NULL,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Initialize default user settings if not exists
    cursor.execute("SELECT COUNT(*) FROM user_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO user_settings 
            (calorie_goal, protein_goal, carbs_goal, fats_goal, water_goal_oz, dietary_preference, activity_level)
            VALUES (2000, 150, 225, 65, 64, 'None', 'moderate')
        """)
    
    conn.commit()
    conn.close()


def get_user_settings() -> Dict[str, Any]:
    """Retrieve user settings from database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM user_settings ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return {}


def update_user_settings(settings: Dict[str, Any]) -> None:
    """Update user settings in database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE user_settings 
        SET calorie_goal = ?, protein_goal = ?, carbs_goal = ?, fats_goal = ?, 
            water_goal_oz = ?, dietary_preference = ?, activity_level = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = (SELECT MAX(id) FROM user_settings)
    """, (
        settings.get('calorie_goal', 2000),
        settings.get('protein_goal', 150),
        settings.get('carbs_goal', 225),
        settings.get('fats_goal', 65),
        settings.get('water_goal_oz', 64),
        settings.get('dietary_preference', 'None'),
        settings.get('activity_level', 'moderate')
    ))
    
    conn.commit()
    conn.close()


def log_food(food_name: str, portion_size: float, unit: str, calories: float, 
             protein: float, carbs: float, fats: float, fiber: float, 
             meal_type: str, logged_date: str) -> None:
    """Log a food entry to database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO food_logs 
        (food_name, portion_size, unit, calories, protein, carbs, fats, fiber, meal_type, logged_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (food_name, portion_size, unit, calories, protein, carbs, fats, fiber, meal_type, logged_date))
    
    conn.commit()
    conn.close()


def get_food_logs(logged_date: str) -> List[Dict[str, Any]]:
    """Retrieve food logs for a specific date."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM food_logs WHERE logged_date = ? ORDER BY logged_at DESC",
        (logged_date,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_food_logs_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Retrieve food logs for a date range."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM food_logs WHERE logged_date BETWEEN ? AND ? ORDER BY logged_date DESC, logged_at DESC",
        (start_date, end_date)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def delete_food_log(log_id: int) -> None:
    """Delete a food log entry."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM food_logs WHERE id = ?", (log_id,))
    
    conn.commit()
    conn.close()


def add_favorite_food(food_name: str, portion_size: float, unit: str, 
                     calories: float, protein: float, carbs: float, 
                     fats: float, fiber: float) -> None:
    """Add a food to favorites."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO favorite_foods 
        (food_name, portion_size, unit, calories, protein, carbs, fats, fiber)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (food_name, portion_size, unit, calories, protein, carbs, fats, fiber))
    
    conn.commit()
    conn.close()


def get_favorite_foods() -> List[Dict[str, Any]]:
    """Retrieve all favorite foods."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM favorite_foods ORDER BY food_name")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def log_water(amount_oz: float, logged_date: str) -> None:
    """Log water intake."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO water_intake (amount_oz, logged_date) VALUES (?, ?)",
        (amount_oz, logged_date)
    )
    
    conn.commit()
    conn.close()


def get_water_intake(logged_date: str) -> float:
    """Get total water intake for a date."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT SUM(amount_oz) as total FROM water_intake WHERE logged_date = ?",
        (logged_date,)
    )
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result[0] else 0.0


def log_weight(weight_lbs: float, logged_date: str) -> None:
    """Log weight entry."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO weight_tracking (weight_lbs, logged_date) VALUES (?, ?)",
        (weight_lbs, logged_date)
    )
    
    conn.commit()
    conn.close()


def get_weight_history(days: int = 30) -> List[Dict[str, Any]]:
    """Get weight history for last N days."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM weight_tracking 
        WHERE logged_date >= date('now', '-' || ? || ' days')
        ORDER BY logged_date DESC
    """, (days,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
