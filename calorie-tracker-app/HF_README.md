# 🥗 AI-Powered Calorie & Macro Tracker

A modern, professional nutrition tracking web app powered by Streamlit, SQLite, and Groq AI.

## ✨ Features

- **📊 Real-time Dashboard** - Track calories, protein, carbs, and fats
- **📈 Weekly Analytics** - Visualize 7-day trends
- **🤖 AI Coach** - Get personalized nutrition advice powered by Groq LLM
- **🔍 Food Database** - Search from 20+ pre-loaded foods
- **💾 Persistent Storage** - SQLite database for data persistence
- **⚙️ Customizable Goals** - Set your daily nutrition targets

## 🎯 Quick Start

### Local Installation

```bash
# Clone or download the project
cd calorie-tracker-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your GROQ_API_KEY to .env

# Run the app
streamlit run app.py
```

### Hugging Face Spaces

Deploy for free on Hugging Face:
1. Create a new Space (Streamlit SDK)
2. Upload all files
3. Add `GROQ_API_KEY` as a secret
4. Done! Your app is live

[See detailed deployment guide](HUGGING_FACE_DEPLOYMENT.md)

## 📱 How to Use

### 1. **Daily Log Tab** 📝
   - Search for foods
   - Enter portion sizes
   - Select meal type
   - Track throughout the day

### 2. **Today's Summary** 📊
   - View daily metrics
   - Check progress toward goals
   - See macro breakdown
   - Get AI nutrition insights

### 3. **Weekly Progress** 📈
   - Analyze 7-day trends
   - View calorie patterns
   - See most logged foods
   - Track consistency

### 4. **Food Database** 🔍
   - Browse all foods
   - Search by name
   - Mark favorites
   - View nutrition details

### 5. **AI Coach** 🤖
   - Chat with personalized nutrition advisor
   - Get meal suggestions
   - Ask diet questions
   - Get insights from your data

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit 1.58.0 |
| Database | SQLite3 |
| AI/LLM | Groq (llama-3.1-8b-instant) |
| LLM Framework | LangChain 1.3.4 |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly |

## 🌟 Sample Foods

**Proteins:** Chicken, Salmon, Eggs, Greek Yogurt  
**Carbs:** Rice, Oatmeal, Sweet Potato, Bread  
**Veggies:** Broccoli, Spinach  
**Fats:** Almonds, Avocado, Peanut Butter  

## 🔑 Get Your Groq API Key

1. Visit [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Create an API key
4. Add to `.env` file: `GROQ_API_KEY=your_key_here`

## 📊 Database Schema

- **user_settings** - Daily goals, preferences
- **food_logs** - Tracked meals with nutrition data
- **favorite_foods** - Bookmarked foods
- **water_intake** - Hydration tracking
- **weight_tracking** - Weight history

## ⚠️ Disclaimer

This app is for educational purposes only. The AI coach is NOT a substitute for professional medical advice. Always consult healthcare professionals before making dietary changes.

## 🚀 Deployment Options

- **Local:** Run with `streamlit run app.py`
- **Hugging Face:** Deploy for free [See guide](HUGGING_FACE_DEPLOYMENT.md)
- **Docker:** Use provided Dockerfile
- **Cloud:** Deploy to Render, Railway, or Heroku

## 📚 Documentation

- [Full Setup Guide](SETUP_COMPLETE.txt)
- [Deployment Instructions](HUGGING_FACE_DEPLOYMENT.md)
- [API Reference](README.md)

## 🎨 Modern UI

- Beautiful gradient design
- Responsive layout
- Smooth animations
- Professional color scheme
- Mobile-friendly interface

## 🤝 Contributing

Found a bug? Want to add a feature? Feel free to submit issues or improvements!

## 📄 License

MIT License - Feel free to use and modify

---

**Made with ❤️ for your health** 🥗💪

Start tracking your nutrition today! 🚀
