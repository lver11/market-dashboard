# 🚀 DashBoard Deployment Guide

## Step 1: Create GitHub Repository

### Option A: Using GitHub CLI (Recommended if installed)

```bash
# Create repository named "DashBoard" on GitHub
gh repo create DashBoard --public --source=. --remote=origin --push

# That's it! Your code is now on GitHub
```

### Option B: Using GitHub Web UI

1. **Go to GitHub**: https://github.com/new
2. **Create new repository**:
   - Repository name: **DashBoard**
   - Description: **Smart Money Market Analysis System with AI-Powered Insights**
   - Visibility: **Public** (or Private)
   - ⚠️ **DO NOT** initialize with README, .gitignore, or license (we already have them)
3. Click **Create repository**
4. Copy the repository URL: `https://github.com/YOUR_USERNAME/DashBoard.git`

### Option C: Manual Git Push (After creating repo on web)

```bash
# Add remote origin (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/DashBoard.git

# Push to GitHub
git push -u origin master

# Or if your main branch is 'main':
git branch -M main
git push -u origin main
```

---

## Step 2: Verify GitHub Repository

1. **Visit your repository**: `https://github.com/YOUR_USERNAME/DashBoard`
2. **Verify files are present**:
   - [x] flask_app.py
   - [x] templates/index.html
   - [x] static/js/app.js
   - [x] static/css/custom.css
   - [x] vercel.json
   - [x] README.md
   - [x] requirements.txt
   - [x] .env.example (NOT .env - this contains API keys!)

---

## Step 3: Deploy to Vercel

### Option A: Using Vercel CLI (Recommended)

1. **Install Vercel CLI** (if not installed):
```bash
npm install -g vercel
```

2. **Login to Vercel**:
```bash
vercel login
```

3. **Deploy from project directory**:
```bash
cd C:\project\DashBoard
vercel
```

4. **Follow the prompts**:
   - **Set up and deploy?** → **Y**
   - **Which scope?** → Select your account
   - **Link to existing project?** → **N**
   - **What's your project's name?** → **DashBoard**
   - **In which directory is your code located?** → **.** (current directory)
   - **Want to override settings?** → **N** (vercel.json will handle it)

5. **Add environment variables**:
```bash
vercel env add GOOGLE_API_KEY
# Paste your Gemini API key when prompted

vercel env add OPENAI_API_KEY
# Paste your OpenAI API key when prompted

vercel env add FRED_API_KEY
# Paste your FRED API key when prompted
```

6. **Deploy to production**:
```bash
vercel --prod
```

### Option B: Using Vercel Web Dashboard

1. **Go to Vercel**: https://vercel.com/new
2. **Import Git Repository**:
   - Click **"Import Project"**
   - Select **"Git"**
   - Choose **"DashBoard"** from your GitHub repositories
3. **Configure Project**:
   - **Project Name**: **DashBoard**
   - **Framework Preset**: **Other** (Vercel will detect Python from vercel.json)
   - **Root Directory**: **.** (leave empty)
   - **Build Command**: *Leave blank* (handled by vercel.json)
   - **Output Directory**: *Leave blank*
4. **Environment Variables**:
   - Click **"Environment Variables"**
   - Add:
     - `GOOGLE_API_KEY` = your Gemini API key
     - `OPENAI_API_KEY` = your OpenAI API key
     - `FRED_API_KEY` = your FRED API key
5. **Click "Deploy"**

---

## Step 4: Verify Deployment

### Check Vercel Dashboard

1. **Visit Vercel dashboard**: https://vercel.com/dashboard
2. **Select "DashBoard" project**
3. **Wait for deployment to complete** (usually 2-3 minutes)
4. **Get your deployment URL**: `https://dashboard-xxxxx.vercel.app`

### Test Live Application

1. **Open deployment URL** in browser
2. **Verify features**:
   - [x] Page loads successfully
   - [x] Market indices display
   - [x] Smart Money Picks table shows data
   - [x] Stock charts render
   - [x] Sector heatmap displays
   - [x] ETF flows section works
   - [x] Economic calendar loads

### Test API Endpoints

```bash
# Test API endpoints
curl https://your-dashboard-url.vercel.app/api/us/stocks
curl https://your-dashboard-url.vercel.app/api/us/heatmap
curl https://your-dashboard-url.vercel.app/api/us/etf-flows
```

---

## 🔧 Troubleshooting

### Issue 1: Build Fails on Vercel

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**: Ensure `requirements.txt` is present and includes all dependencies.

### Issue 2: API Returns 404

**Error**: Endpoints not found

**Solution**: Check `vercel.json` routes configuration matches Flask routes.

### Issue 3: AI Features Show "API Key Missing"

**Error**: AI analysis not loading

**Solution**: Ensure environment variables are set in Vercel dashboard:
- Go to Project → Settings → Environment Variables
- Add missing keys and redeploy

### Issue 4: Static Files Not Loading

**Error**: CSS/JS files return 404

**Solution**: Verify `static/` folder is committed to Git and `vercel.json` includes static file routes.

---

## 📊 Post-Deployment Checklist

- [ ] GitHub repository created and pushed
- [ ] All files visible on GitHub (except .env)
- [ ] Vercel project created
- [ ] Environment variables configured in Vercel
- [ ] Deployment successful (green checkmark)
- [ ] Live URL accessible
- [ ] All API endpoints working
- [ ] Frontend UI renders correctly
- [ ] AI features functional (if API keys provided)

---

## 🎯 Custom Domain (Optional)

### Set Up Custom Domain on Vercel

1. **Go to Vercel Project → Settings → Domains**
2. **Enter your domain**: `dashboard.yourdomain.com`
3. **Follow DNS instructions** provided by Vercel
4. **Wait for SSL certificate** to be issued (automatic)

---

## 🔄 Continuous Deployment

Vercel automatically deploys when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Add new feature"
git push origin master

# Vercel will automatically deploy your changes!
```

---

## 📝 Notes

- **.env file is gitignored** - API keys won't be uploaded to GitHub
- **Environment variables must be set in Vercel dashboard** - They are not in the code
- **Cold starts** - First load may take 2-3 seconds (serverless Python)
- **Rate limits** - Free Vercel tier has bandwidth limits
- **Data updates** - Market data is cached; run `update_all.py` periodically to refresh

---

## 🎉 Success!

Your DashBoard is now live on Vercel!

**Live URL**: `https://dashboard-xxxxx.vercel.app`
**GitHub**: `https://github.com/YOUR_USERNAME/DashBoard`

**Enjoy your smart money market analysis platform! 🚀**
