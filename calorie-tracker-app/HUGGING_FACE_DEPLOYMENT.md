# 🚀 Deploy to Hugging Face Spaces

## Quick Start

This guide will help you deploy the Calorie Tracker app to Hugging Face Spaces for free!

### Prerequisites
- Hugging Face account (free at https://huggingface.co)
- Git installed
- Your Groq API key

---

## Step 1: Create a Hugging Face Space

1. Go to https://huggingface.co/new-space
2. Fill in the form:
   - **Owner:** Your username
   - **Space name:** `calorie-tracker` (or your choice)
   - **License:** MIT (recommended)
   - **Space SDK:** Streamlit
   - **Private/Public:** Your choice
3. Click "Create Space"

---

## Step 2: Upload Your Files

### Option A: Using Git (Recommended)

```bash
# Clone your space
git clone https://huggingface.co/spaces/YOUR_USERNAME/calorie-tracker
cd calorie-tracker

# Copy your app files
cp /Users/roja/Desktop/Python/calorie-tracker-app/* .

# Add all files
git add .

# Commit
git commit -m "Initial commit: Calorie Tracker app"

# Push to Hugging Face
git push
```

### Option B: Using Web Interface (Easier)

1. Go to your space page
2. Click "Add file" → "Upload files"
3. Upload:
   - `app.py`
   - `requirements.txt`
   - `utils/` folder
   - `components/` folder
   - `README.md` (optional)

---

## Step 3: Set Up Environment Variables

1. Go to your Space settings
2. Click "Repository secrets" or "Secrets and tokens"
3. Add a new secret:
   - **Name:** `GROQ_API_KEY`
   - **Value:** Your Groq API key from https://console.groq.com

---

## Step 4: Configure Streamlit Settings (Optional)

Create `.streamlit/config.toml`:

```toml
[client]
showErrorDetails = true

[server]
maxUploadSize = 200
enableXsrfProtection = true

[theme]
primaryColor = "#667eea"
backgroundColor = "#f5f7fa"
secondaryBackgroundColor = "#e2e8f0"
textColor = "#2d3748"
font = "sans serif"
```

---

## Step 5: Launch!

Once files are uploaded, Hugging Face will automatically:
1. Install dependencies from `requirements.txt`
2. Launch your Streamlit app
3. Give you a public URL

Your app will be live at: `https://huggingface.co/spaces/YOUR_USERNAME/calorie-tracker`

---

## 🎯 Important Notes

### Data Persistence
- **SQLite database** is stored locally on the Hugging Face server
- Data persists between sessions
- Gets reset when you redeploy

### API Key Security
- Never commit `.env` file
- Use Hugging Face Secrets (steps above)
- The app will automatically load from environment variables

### Performance
- Free tier is limited but sufficient for personal use
- App may sleep after inactivity
- Wakes up on first request

### Database
- Database file (`nutrition_db.sqlite`) will be created automatically
- Stores data in `/tmp` or persistent storage

---

## 🔧 Troubleshooting

### Issue: "GROQ_API_KEY not set"
**Solution:** Make sure you added the secret in Hugging Face Space settings

### Issue: Import errors
**Solution:** Make sure all dependencies are in `requirements.txt`

### Issue: Database not persisting
**Solution:** This is expected on free tier. Consider using a cloud database (PostgreSQL on Render, etc.)

---

## 📦 Alternative: Use Docker

If you want more control, create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["streamlit", "run", "app.py", "--server.port=7860"]
```

---

## 🌐 Share Your App

Once deployed, share the link:
- **Public Link:** `https://huggingface.co/spaces/YOUR_USERNAME/calorie-tracker`
- **Embed Code:** Get from Space settings → Share tab
- **Social Media:** Share with friends!

---

## 💡 Pro Tips

1. **Add a thumbnail** - Makes your space look professional
2. **Write a README** - Explain what your app does
3. **Add tags** - nutrition, fitness, health
4. **Enable comments** - Let users give feedback
5. **Monitor usage** - Check Space settings for analytics

---

## Next Steps

1. Create your Hugging Face account
2. Create a new Space (Streamlit)
3. Upload your files
4. Set your GROQ_API_KEY secret
5. Wait for deployment (1-2 minutes)
6. Share your app with the world! 🎉

---

## Resources

- [Hugging Face Spaces Docs](https://huggingface.co/docs/hub/spaces)
- [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)
- [Hugging Face Git Guide](https://huggingface.co/docs/hub/repositories-getting-started)

---

**Your app is ready to go public!** 🚀
