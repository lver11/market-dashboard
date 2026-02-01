#!/bin/bash
# 🚀 DashBoard Quick Deployment Script
# Run this script to deploy DashBoard to GitHub and Vercel

set -e

echo "======================================"
echo "🚀 DashBoard Deployment Script"
echo "======================================"
echo ""

# Check if gh CLI is installed
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI detected"

    # Create repository and push
    echo "📦 Creating GitHub repository 'DashBoard'..."
    gh repo create DashBoard --public --source=. --remote=origin --push

    echo "✅ Repository created and code pushed to GitHub!"
    echo "📍 Repository URL: $(git config --get remote.origin.url)"
else
    echo "⚠️  GitHub CLI not found"
    echo ""
    echo "Please create repository manually:"
    echo "1. Go to: https://github.com/new"
    echo "2. Repository name: DashBoard"
    echo "3. Description: Smart Money Market Analysis System"
    echo "4. DO NOT initialize with README or .gitignore"
    echo "5. Click 'Create repository'"
    echo ""
    echo "Then run these commands:"
    echo '  git remote add origin https://github.com/YOUR_USERNAME/DashBoard.git'
    echo '  git branch -M main'
    echo '  git push -u origin main'
    echo ""
    exit 1
fi

echo ""
echo "======================================"
echo "🌐 Deploying to Vercel..."
echo "======================================"
echo ""

# Check if vercel CLI is installed
if command -v vercel &> /dev/null; then
    echo "✅ Vercel CLI detected"

    # Deploy to Vercel
    echo "📦 Deploying to Vercel..."
    vercel

    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "📝 Don't forget to add environment variables:"
    echo "   vercel env add GOOGLE_API_KEY"
    echo "   vercel env add OPENAI_API_KEY"
    echo "   vercel env add FRED_API_KEY"
    echo ""
    echo "   Then deploy to production:"
    echo "   vercel --prod"
else
    echo "⚠️  Vercel CLI not found"
    echo ""
    echo "Please install Vercel CLI:"
    echo "   npm install -g vercel"
    echo ""
    echo "Then deploy manually:"
    echo "1. Go to: https://vercel.com/new"
    echo "2. Import 'DashBoard' repository from GitHub"
    echo "3. Configure environment variables in Vercel dashboard"
    echo "4. Click 'Deploy'"
fi

echo ""
echo "======================================"
echo "✅ Deployment Script Complete!"
echo "======================================"
echo ""
echo "📚 For detailed instructions, see: DEPLOYMENT_GUIDE.md"
echo ""
