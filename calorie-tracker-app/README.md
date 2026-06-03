# 🥗 AI-Powered Calorie & Macro Tracker

A production-quality Streamlit application that helps you track your daily nutrition intake with AI-powered insights and personalized coaching.

## ✨ Features

### 📝 Daily Food Log
- Search a comprehensive nutrition database
- Log foods with custom portion sizes
- Track calories and macros per meal (Breakfast, Lunch, Dinner, Snacks)
- Edit and delete logged entries
- Store all data in SQLite database

### 📊 Today's Summary
- Real-time metrics for calories and macros
- Progress indicators showing consumption vs. goals
- Visual donut charts for calorie and macro breakdown
- Meal-by-meal breakdown visualization
- Water intake tracker
- AI-generated personalized nutrition insights

### 📈 Weekly Progress
- 7-day trend analysis with interactive charts
- Line chart showing daily calorie trends
- Stacked bar chart for macro breakdowns
- Weekly statistics (averages, most logged foods)
- Historical daily data table

### 🔍 Nutrition Database
- Browse 20+ common foods with complete nutrition info
- Search functionality for easy food discovery
- Add foods to favorites for quick logging
- View macronutrient and micronutrient breakdowns

### 🤖 AI Nutrition Coach
- Interactive chat interface powered by Groq LLM
- Ask personalized nutrition questions
- Get meal suggestions based on your goals
- Identify patterns in your eating habits
- Receive encouragement and actionable advice
- Chat history maintained throughout your session

### ⚙️ Customizable Settings
- Daily calorie goal (default: 2000)
- Daily macro targets (protein, carbs, fats)
- Water intake goal
- Dietary preferences (Vegan, Vegetarian, Keto)
- Activity level configuration

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Database:** SQLite
- **AI/LLM:** Groq + LangChain
- **Data Processing:** Pandas, NumPy
- **Visualization:** Plotly
- **Package Manager:** uv
- **Food Data:** Local nutrition database (expandable to USDA FoodData Central)

## 📁 Project Structure

```
calorie-tracker-app/
│
├── app.py                          # Main Streamlit application
├── pyproject.toml                  # Project dependencies
├── .env.example                    # Environment variables template
├── README.md                       # This file
│
├── data/
│   └── nutrition_db.sqlite         # SQLite database (created on first run)
│
├── utils/
│   ├── __init__.py
│   ├── database.py                 # Database operations
│   ├── nutrition_calc.py           # Nutrition calculations
│   ├── food_search.py              # Food database search
│   ├── data_processing.py          # Data validation & utilities
│   └── llm_agent.py                # Groq + LangChain integration
│
└── components/
    ├── __init__.py
    ├── settings_sidebar.py         # User settings sidebar
    ├── daily_log_tab.py            # Daily food logging tab
    ├── today_summary_tab.py        # Today's nutrition summary
    ├── weekly_progress_tab.py      # Weekly trends & analysis
    ├── nutrition_search_tab.py     # Food database browser
    └── ai_coach_tab.py             # AI nutrition coach chat
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- uv (modern Python package manager)
- Groq API key (free tier available at https://console.groq.com)

### Installation

1. **Clone or extract the project**
```bash
cd /Users/roja/Desktop/Python/calorie-tracker-app
```

2. **Install dependencies using uv**
```bash
uv sync
```

3. **Set up environment variables**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=your_api_key_here
```

4. **Run the application**
```bash
uv run streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## 📖 Usage Guide

### Logging Foods

1. Go to the **📝 Daily Log** tab
2. Search for a food (e.g., "chicken breast")
3. Select the food from the search results
4. Adjust the portion size if needed
5. Choose the meal type (Breakfast, Lunch, Dinner, Snack)
6. Click "➕ Add Food"

### Tracking Progress

- **Today's Summary**: Check real-time progress toward daily goals with visual indicators
- **Weekly Progress**: Analyze trends over 7 days with charts and statistics
- **AI Insights**: Click "🔄 Generate Insight" to get AI-powered feedback on your nutrition

### Using the AI Coach

1. Go to the **🤖 AI Coach** tab
2. Ask any nutrition-related question
3. The coach has access to your:
   - Today's food logs
   - Last 7 days of history
   - Personal goal targets
   - Most frequently logged foods

### Managing Settings

1. Adjust your daily goals in the sidebar
2. Set your dietary preferences
3. Configure your activity level
4. Click "💾 Save Settings" to persist changes

## 📊 Sample Nutrition Data

The app includes 20 pre-loaded common foods:
- Chicken Breast, Salmon, Beef
- Eggs, Greek Yogurt, Cottage Cheese
- Broccoli, Spinach, Sweet Potato
- Brown Rice, Oatmeal, Whole Wheat Bread
- Almonds, Avocado, Peanut Butter
- And more...

You can expand this by modifying `utils/food_search.py`

## 🧮 Nutrition Calculations

### Daily Totals
- **Calories:** Sum of all logged foods
- **Macros:** Protein, Carbs, Fats calculated from portion sizes
- **Remaining:** Goal minus consumed amount

### Macro Breakdown Percentage
- Protein: 4 calories per gram
- Carbs: 4 calories per gram
- Fats: 9 calories per gram

### Weekly Averages
- Calculated from daily totals for the past 7 days
- Shows eating patterns and consistency

## 🤖 AI Nutrition Coach Features

### LangChain Integration
- **PromptTemplates** for consistent prompt formatting
- **Chains** for multi-step nutrition analysis
- **ConversationBufferMemory** for maintaining chat history

### Sample Questions You Can Ask
- "What should I eat for lunch to hit my protein goal?"
- "Am I eating too many carbs?"
- "What foods have I logged the most this week?"
- "How's my macro balance today?"
- "Give me a healthy meal plan for tomorrow"
- "Why am I consistently under my protein goal?"

### Important Disclaimers
- The AI coach is not a doctor or registered dietitian
- Advice is for educational purposes only
- Always consult healthcare professionals for medical advice
- The app should not be used for diagnosing or treating medical conditions

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

### Customizing Daily Goals
Edit the defaults in `components/settings_sidebar.py`:
```python
calorie_goal = 2000        # Default daily calorie target
protein_goal = 150         # Default daily protein (grams)
carbs_goal = 225          # Default daily carbs (grams)
fats_goal = 65            # Default daily fats (grams)
water_goal_oz = 64        # Default daily water (oz)
```

## 📚 API Reference

### Database Functions (utils/database.py)
- `init_db()` - Initialize SQLite database
- `log_food()` - Add food entry
- `get_food_logs()` - Retrieve logs for a date
- `add_favorite_food()` - Save food to favorites
- `log_water()` - Track water intake
- `log_weight()` - Track weight

### Nutrition Calculations (utils/nutrition_calc.py)
- `calculate_daily_totals()` - Sum macros for the day
- `calculate_remaining()` - Calculate remaining budget
- `get_meal_breakdown()` - Breakdown by meal type
- `calculate_weekly_averages()` - 7-day statistics
- `get_color_status()` - Determine status color

### Food Search (utils/food_search.py)
- `search_foods()` - Query food database
- `get_all_foods()` - Retrieve all foods
- `calculate_nutrition_for_portion()` - Scale macros to portion size

## 🚨 Troubleshooting

### "GROQ_API_KEY not set"
- Ensure `.env` file is created in the project root
- Verify your API key is correct
- Restart the Streamlit app: press `Ctrl+C` and run `uv run streamlit run app.py`

### Database errors
- The database is auto-initialized on first run
- Check that the `data/` directory has write permissions
- Database file: `data/nutrition_db.sqlite`

### Import errors when running
- Run `uv sync` to ensure all dependencies are installed
- Verify you're using `uv run streamlit run app.py` (not just `streamlit run app.py`)

### Slow LLM responses
- This is normal for the first request
- Groq's free tier has rate limits
- Consider caching responses for frequently asked questions

## 📈 Future Enhancements

- [ ] Integration with USDA FoodData Central API
- [ ] Recipe creation and logging
- [ ] Barcode scanner for food logging
- [ ] Export nutrition reports to PDF
- [ ] Weight and body measurements tracking
- [ ] Meal planning with AI
- [ ] Social features (share meals, challenges)
- [ ] Integration with fitness trackers
- [ ] Custom food database per user
- [ ] Multi-language support

## 📜 License

This project is open-source and available for personal and educational use.

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the project
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📧 Support

For issues, questions, or suggestions, please open an issue in the repository.

## ⚠️ Medical Disclaimer

This application is for informational and educational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider before making significant changes to your diet or exercise routine.

**The creators of this app are not responsible for any health consequences resulting from the use of this application.**

---

**Happy tracking! 🎉 Maintain a healthy lifestyle with data-driven nutrition insights.**
