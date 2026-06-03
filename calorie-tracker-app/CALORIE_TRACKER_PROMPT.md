# Refined Prompt: AI-Powered Calorie & Macro Tracker

You are an expert Python full-stack developer and AI engineer. Build a production-quality AI-powered Streamlit app that acts as my personal Nutrition & Fitness Companion.

The app should allow me to track daily food intake, log meals throughout the day, visualize macro and calorie consumption, monitor progress against daily targets, and provide AI-powered nutrition insights using Groq.

Use the following stack strictly:
- **Frontend/App Framework:** Streamlit
- **Food Database:** USDA FoodData Central API or local nutrition database (nutritionix)
- **LLM Provider:** Groq
- **LLM Framework:** LangChain for prompt management and LLM orchestration
- **Package and virtual environment management:** uv only
- **Charts:** Plotly or Streamlit-compatible charts
- **Data processing:** pandas, numpy
- **Nutritional calculations:** custom Python logic
- **Database:** SQLite for storing daily logs and user preferences

---

## Core Requirements

Create a Streamlit app with exactly 5 tabs:
1. **Daily Food Log**
2. **Today's Summary**
3. **Weekly Progress**
4. **Nutrition Database Search**
5. **AI Nutrition Coach**

---

## Tab 1: Daily Food Log

Create a tab named **Daily Food Log**.

### Features:
- Date picker to select a specific day (default: today)
- Search box to find foods from the nutrition database
- Display search results with nutrition info (calories, protein, carbs, fats, fiber)
- Add foods with portion size in grams or standard servings
- Display time of meal (Breakfast, Lunch, Dinner, Snack)
- Show all logged foods for the selected day in a table with:
  - Food name
  - Portion size
  - Calories
  - Protein (g)
  - Carbs (g)
  - Fats (g)
  - Fiber (g)
  - Action to delete/edit entry
- Store all food logs in SQLite database with timestamp
- Allow editing of portion sizes

---

## Tab 2: Today's Summary

Create a tab named **Today's Summary**.

### Features:
- Display metric cards for:
  - **Total Calories Consumed** vs. Daily Goal
  - **Total Protein (g)** vs. Daily Goal
  - **Total Carbs (g)** vs. Daily Goal
  - **Total Fats (g)** vs. Daily Goal
- Remaining calories and macros for the day
- Circular progress indicators or donut charts showing:
  - Calorie consumption percentage
  - Macro breakdown (Protein %, Carbs %, Fats %)
- Horizontal bar chart showing macronutrient distribution
- Meal breakdown:
  - Calories and macros per meal (Breakfast, Lunch, Dinner, Snacks)
  - Visual bar chart of meal distribution
- Water intake tracker:
  - Input field to log water (in oz or ml)
  - Progress toward daily water goal
- **AI Nutrition Insight:** Use Groq LLM to generate:
  - 2-3 sentence personalized feedback on today's nutrition
  - Highlight if macros are balanced or imbalanced
  - Suggest adjustments if needed
  - Mention if calorie goal is on track

---

## Tab 3: Weekly Progress

Create a tab named **Weekly Progress**.

### Features:
- Calendar view or table showing last 7 days of logs
- Line chart showing daily calorie trends
- Stacked bar chart showing daily macro breakdown
- Summary statistics:
  - Average daily calories
  - Average daily macros
  - Most logged foods this week
  - Days goal was met (both calories and macros)
- Comparison to weekly goals
- Trend analysis (weekly trend up/down)

---

## Tab 4: Nutrition Database Search

Create a tab named **Nutrition Database Search**.

### Features:
- Search functionality to browse available foods
- Display nutrition info:
  - Standard serving size
  - Calories per serving
  - Macronutrient breakdown
  - Micronutrients (sodium, sugar, fiber)
- Favorite foods list:
  - Save frequently used foods
  - Quick-add to today's log
  - Save custom serving sizes
- Food categories/filters:
  - Proteins (meats, legumes, dairy)
  - Vegetables
  - Fruits
  - Grains
  - Snacks
  - Beverages

---

## Tab 5: AI Nutrition Coach

Create a tab named **AI Nutrition Coach**.

### Features:
- Interactive chat interface using Streamlit
- Maintain chat history using session state
- Pass context to LLM:
  - Daily food logs (last 7 days)
  - Current day's consumption
  - Daily/weekly averages
  - Goal progress
  - Personal nutritional targets
- User can ask questions such as:
  - "What should I eat for lunch to hit my protein goal?"
  - "Am I eating too many carbs?"
  - "What foods have I logged the most this week?"
  - "How's my macro balance today?"
  - "Give me a healthy meal plan for tomorrow based on my goals"
  - "Why am I consistently under my protein goal?"
  - "What are the best protein sources I've logged?"
- AI should:
  - Provide evidence-based nutrition advice
  - Suggest meal ideas based on logged history
  - Identify nutritional patterns
  - Give gentle encouragement or adjustments
  - Include disclaimer that advice is for educational purposes and not medical advice
  - Not provide extreme or unsafe advice

---

## User Settings & Configuration

### Create a sidebar for user settings:
- Daily calorie goal (default: 2000)
- Daily protein goal (default: 150g or based on body weight)
- Daily carbs goal (default: 225g)
- Daily fats goal (default: 65g)
- Daily water goal (default: 64 oz or 2L)
- Dietary preferences (Vegan, Vegetarian, Keto, None)
- Weight tracking (optional):
  - Log weight
  - View weight trend chart
- Activity level for calorie calculations

---

## Groq + LangChain LLM Requirements

Use Groq with LangChain for all AI features.

### Requirements:
- Read Groq API key from environment variable: `GROQ_API_KEY`
- Do not hardcode API keys
- Create reusable LangChain + Groq client wrapper in `utils/llm_agent.py`
- Use LangChain's `ChatGroq` for LLM integration
- Implement LangChain `PromptTemplate` for consistent prompt formatting
- Use LangChain chains for multi-step operations (e.g., context → analysis → response)
- Use LangChain memory/history management for chat context
- Use configurable model name: `llama-3.1-8b-instant` or another available Groq model
- LLM responses should be:
  - Concise and practical
  - Grounded in user's nutrition data
  - Encouraging but honest
  - Evidence-based
- Include graceful error handling for:
  - Missing API key
  - Groq API call failures
  - Empty responses
  - LangChain chain execution errors

---

## Required Project Structure

```
calorie-tracker-app/
│
├── app.py
│
├── pyproject.toml
├── uv.lock
├── README.md
├── .env.example
├── .gitignore
│
├── data/
│   └── nutrition_db.sqlite
│
├── utils/
│   ├── __init__.py
│   ├── data_processing.py
│   ├── nutrition_calc.py
│   ├── database.py
│   ├── food_search.py
│   └── llm_agent.py
│
└── components/
    ├── __init__.py
    ├── daily_log_tab.py
    ├── today_summary_tab.py
    ├── weekly_progress_tab.py
    ├── nutrition_search_tab.py
    ├── settings_sidebar.py
    └── ai_coach_tab.py
```

---

## File Responsibilities

### app.py
- Main Streamlit entry point
- Configure page title, icon, and layout
- Create 5 tabs
- Initialize session state and database
- Call settings sidebar
- Call each tab component

### utils/data_processing.py
- Food search and validation
- CSV/JSON nutrition data loading
- Food name normalization
- Portion size conversion (grams to standard servings)

### utils/nutrition_calc.py
- Calculate daily totals from logged foods
- Calculate remaining calories/macros
- Generate meal breakdown
- Calculate weekly averages
- Calorie deficit/surplus calculation
- Macro percentage calculations

### utils/database.py
- SQLite database initialization
- Store/retrieve daily food logs
- Store/retrieve user settings
- Store/retrieve favorite foods
- Store weight tracking history
- Query functions for weekly/monthly data

### utils/food_search.py
- Search nutrition database (USDA FoodData Central or nutritionix API)
- Format and cache search results
- Handle API calls with error handling

### utils/llm_agent.py
- LangChain + Groq client setup
- LangChain PromptTemplate creation and management
- LangChain chain orchestration for multi-step operations
- Prompt construction with nutrition context
- AI nutrition insights generation using LangChain chains
- Chat response generation with memory management
- Error handling for missing API key and LangChain execution errors

### components/daily_log_tab.py
- Date picker
- Food search interface
- Add food with portion size
- Display logged foods table
- Delete/edit functionality

### components/today_summary_tab.py
- Metric cards for calories and macros
- Progress indicators/donuts
- Macro distribution charts
- Meal breakdown visualization
- Water intake tracker
- AI-generated nutrition insight

### components/weekly_progress_tab.py
- Calendar or table view of 7-day history
- Line chart for calorie trends
- Stacked bar chart for macro trends
- Summary statistics
- Week comparison

### components/nutrition_search_tab.py
- Search bar with filters
- Display nutrition database results
- Favorite foods management
- Food categories

### components/settings_sidebar.py
- User goal configuration
- Dietary preferences
- Weight tracking
- Activity level settings

### components/ai_coach_tab.py
- Chat interface
- Chat history display
- Nutrition context passing to Groq
- Response formatting with disclaimers

---

## uv Requirements

Use uv strictly.

### Setup instructions in README:
```bash
uv sync
uv run streamlit run app.py
```

### Dependencies to install:
```bash
uv add streamlit pandas numpy plotly groq python-dotenv langchain langchain-groq
uv add requests  # for API calls
uv add sqlalchemy  # for database ORM (optional)
```

Do not use pip, venv, conda, poetry, or requirements.txt.

---

## Environment Variables

Create `.env.example` with:
```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

Use python-dotenv to load environment variables.

---

## Streamlit UI Requirements

- Use `st.set_page_config` with wide layout
- Use tabs for main navigation
- Use metric cards for KPIs
- Use clear section headers
- Use helpful info, warning, and error messages
- Show helpful prompts for users new to the app
- Cache API calls where appropriate
- Format calories and macros clearly
- Use color coding:
  - Green: Goal met or good progress
  - Yellow: Close to goal
  - Red: Below/above goal
- Responsive design that works on mobile and desktop

---

## Data and Calculation Edge Cases

Handle these cases:
- Empty food logs
- Invalid portion sizes
- Food not found in database
- API failures for food search
- Missing user settings (use defaults)
- Unusual macro goals
- Users with very high/low calorie goals
- Missing Groq API key
- Duplicate food entries
- Invalid dates

---

## AI Safety and Accuracy Requirements

The AI coach should:
- Clearly state it is not a doctor or nutritionist
- Include disclaimer that advice is for educational use only
- Avoid extreme diet recommendations
- Not diagnose or treat medical conditions
- Base suggestions on logged data, not speculation
- Recommend consulting healthcare providers for serious concerns
- Provide evidence-based information (cite general nutrition science)
- Be encouraging and non-judgmental
- Say when it lacks information to answer

---

## README Requirements

Create a README.md containing:
- Project overview and features
- Folder structure
- Setup instructions using uv only
- Environment variable setup
- How to run the app
- Supported food databases
- How to add custom foods
- Nutrition calculation methodology
- Screenshots (optional)
- Disclaimer for educational use only

---

## Sample CSV for Initial Data

Include sample food data for testing:
```
food_name,serving_size,unit,calories,protein,carbs,fats,fiber,sodium
Chicken Breast,100,g,165,31,0,3.6,0,74
Broccoli,100,g,34,2.8,7,0.4,2.4,64
Brown Rice,100,g,111,2.6,23,0.9,1.8,7
Salmon,100,g,208,20,0,13,0,59
Almonds,28,g,164,6,6,14,3.5,0
Banana,118,g,105,1.3,27,0.3,3.1,2
```

---

## Expected Final Output

Generate the complete working project with all files.

The final app should be runnable with:
```bash
uv run streamlit run app.py
```

Before finishing, verify that:
- Project structure is correct
- All imports work
- App runs without syntax errors
- Food search works
- Daily logging functionality works
- Calculations are accurate
- All 5 tabs render properly
- Groq insights generate when API key is provided
- App handles missing API key gracefully
- Database persists data correctly
- README contains uv-only setup instructions
- UI is clean and user-friendly
