# Render Deployment - Quick Start Guide

## 📋 Checklist for Deployment

### Step 1: Access Render Dashboard
- [ ] Visit https://dashboard.render.com
- [ ] Log in with your GitHub account

### Step 2: Check DashBoard Service Status
- [ ] Find "DashBoard" service in dashboard
- [ ] Check deployment status (Building, Live, etc.)
- [ ] Click on DashBoard service

### Step 3: Verify Deployment
- [ ] Check if service is "Live"
- [ ] Click the provided URL to test
- [ ] Expected URL: https://[your-service-name].onrender.com

### Step 4: If Not Connected to GitHub
If you don't see DashBoard service or it's not connected:

1. **Create New Web Service**:
   - Click "New +"
   - Select "Web Service"
   - Click "Connect GitHub"
   - Select "taewook486/DashBoard" repository
   - Click "Connect"

2. **Configure Service**:
   ```
   Name: DashBoard
   Region: Oregon (or your preferred region)
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python flask_app.py
   ```

3. **Environment Variables**:
   ```
   PYTHON_VERSION: 3.10.0
   PORT: 5001
   ```

4. **Create Service**:
   - Click "Create Web Service"
   - Wait 3-5 minutes for build
   - Service will auto-deploy on future pushes to main branch

### Step 5: After Deployment
- [ ] Wait for build to complete (check "Logs" tab)
- [ ] Visit the live URL
- [ ] Test all functionality:
   - [ ] Main page loads
   - [ ] API endpoints respond (200 OK)
   - [ ] Smart Money table displays
   - [ ] Charts render correctly

## 🔍 Troubleshooting

### Build Failed?
- Check "Logs" tab for error messages
- Common issues:
  - Missing dependencies → Check requirements.txt
  - Import errors → Check file structure
  - Port conflicts → PORT env var set to 5001

### Service Not Responding?
- Check "Events" tab for recent errors
- Verify environment variables are set
- Check if server is actually running

### GitHub Not Connected?
- Go to Settings → Connect GitHub
- Re-authorize Render access to repository
- Ensure "web" service type is selected

## 🧪 Quick Test Commands

```bash
# Test main page
curl https://[your-url].onrender.com/

# Test API endpoints
curl https://[your-url].onrender.com/api/us/stocks
curl https://[your-url].onrender.com/api/us/heatmap
curl https://[your-url].onrender.com/api/us/indices
```

## ✅ Success Criteria

- [ ] Service status shows "Live"
- [ ] URL loads without errors
- [ ] API endpoints return 200 OK
- [ ] Frontend displays correctly
- [ ] No errors in Render logs

## 📝 After Deployment

Once deployed and working:

1. **Update render.yaml if needed** (already configured correctly)
2. **Set up custom domain** (optional)
3. **Configure auto-deployment** (enabled if GitHub connected)
4. **Monitor performance** (check Render dashboard regularly)

---

**Current Status:**
- GitHub commits: Up to date
- Last commit: 4a70930 (Trigger: Force Render deployment)
- Expected deployment: Auto-triggered if GitHub connected

**Next Step:**
Visit https://dashboard.render.com to verify deployment status
