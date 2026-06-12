# Git & GitHub Setup Guide for SYNOP Decoder Project

## 📋 Table of Contents
- [Initial Setup (One-Time)](#initial-setup-one-time)
- [Push to GitHub](#push-to-github)
- [Collaborate with Teammate](#collaborate-with-teammate)
- [Common Git Commands](#common-git-commands)
- [Branching Strategy](#branching-strategy)
- [Pull Requests & Merging](#pull-requests--merging)

---

## 🎯 Initial Setup (One-Time)

### Step 1: Install Git
Download and install from: https://git-scm.com/download/win

### Step 2: Configure Git (First time only)
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 3: Navigate to Project Directory
```bash
cd "D:\IMD internship"
```

### Step 4: Initialize Git Repository
```bash
git init
```

### Step 5: Create .gitignore File
Create a file named `.gitignore` in the project root:
```bash
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project-specific
*.log
temp/
.env
synop_*.csv
synop_*.json
synop_*.txt
```

---

## 📤 Push to GitHub

### Step 1: Create Repository on GitHub
1. Go to https://github.com/new
2. **Repository name:** `synop-decoder` (or your choice)
3. **Description:** FM-12 SYNOP Decoder for India Meteorological Department
4. **Public/Private:** Choose (Public for sharing, Private for internal)
5. **Initialize:** Leave unchecked (you already have files)
6. Click **"Create repository"**

### Step 2: Add Files to Git
```bash
cd "D:\IMD internship"
git add .
```

### Step 3: Create Initial Commit
```bash
git commit -m "Initial commit: SYNOP decoder with CLI and REST API"
```

### Step 4: Add Remote Repository
```bash
git remote add origin https://github.com/YOUR_USERNAME/synop-decoder.git
```

### Step 5: Push to GitHub
```bash
git branch -M main
git push -u origin main
```

**That's it!** Your project is now on GitHub! 🎉

---

## 👥 Collaborate with Teammate

### Option A: Add Teammate as Collaborator (Easiest)

1. **Go to your GitHub repo**
2. Click **Settings** → **Collaborators**
3. Click **Add people**
4. Enter teammate's GitHub username
5. Send them the invite link
6. Teammate accepts the invite ✅

### Option B: Team-Based Access (For Organizations)

1. Create an organization on GitHub
2. Add both of you as members
3. Create the repo under the organization
4. Both can push/pull directly

---

## 🔄 Workflow for You & Your Teammate

### First Time Teammate Setup
```bash
# Clone the repo to their computer
git clone https://github.com/YOUR_USERNAME/synop-decoder.git
cd synop-decoder

# Configure their Git
git config user.name "Teammate Name"
git config user.email "teammate@example.com"
```

### Daily Workflow (Pull Latest Changes)
```bash
# Before starting work
git pull origin main

# Make changes to files
# (Edit code, add features, etc.)

# Check what changed
git status

# Add changes
git add .

# Commit with message
git commit -m "Add batch export feature"

# Push to GitHub
git push origin main
```

---

## 🌿 Branching Strategy (Recommended)

### For Better Collaboration, Use Branches:

```bash
# Create a feature branch
git checkout -b feature/add-database

# Make changes and commit
git add .
git commit -m "Add database support"

# Push branch to GitHub
git push origin feature/add-database

# Create Pull Request on GitHub (for review)
# After review, merge to main
```

### Branch Naming Convention
```
main                    # Production/stable code
develop                 # Development version
feature/new-feature     # New features
bugfix/fix-issue        # Bug fixes
api/endpoint-name       # API additions
```

---

## 📋 Common Git Commands

### Status & Viewing
```bash
# See current status
git status

# See recent commits
git log --oneline -5

# See changes you made
git diff

# See all branches
git branch -a
```

### Committing
```bash
# Stage specific file
git add filename.py

# Stage all changes
git add .

# Commit with message
git commit -m "Descriptive message"

# Amend last commit (if not pushed)
git commit --amend -m "New message"
```

### Pushing & Pulling
```bash
# Pull latest changes
git pull origin main

# Push your changes
git push origin main

# Pull and push specific branch
git pull origin feature/name
git push origin feature/name
```

### Branching
```bash
# Create new branch
git checkout -b feature/name

# Switch to existing branch
git checkout main

# Delete local branch
git branch -d feature/name

# Delete remote branch
git push origin --delete feature/name
```

---

## 🔀 Pull Requests & Merging

### Teammate Creates Pull Request
1. Teammate creates and pushes a feature branch
2. On GitHub, they click **"New Pull Request"**
3. Select: `base: main` ← `compare: feature/name`
4. Add description of changes
5. Click **"Create Pull Request"**

### Review & Merge
1. You review the code changes
2. If good: Click **"Merge Pull Request"**
3. Confirm merge
4. Delete the feature branch ✅

### OR: Merge Locally
```bash
# Pull the branch
git pull origin feature/name

# Switch to main
git checkout main

# Merge branch
git merge feature/name

# Push to GitHub
git push origin main
```

---

## 📊 Team Workflow Example

```
Day 1 (You):
  git clone https://github.com/yourrepo/synop-decoder.git
  git checkout -b feature/add-export
  # Edit code
  git add .
  git commit -m "Add CSV export"
  git push origin feature/add-export
  # Create Pull Request on GitHub

Day 1 (Teammate):
  git clone https://github.com/yourrepo/synop-decoder.git
  git pull origin main
  git checkout -b feature/add-api-docs
  # Edit code
  git add .
  git commit -m "Add API documentation"
  git push origin feature/add-api-docs
  # Create Pull Request on GitHub

Day 2:
  # You review teammate's PR → Merge
  git pull origin main
  git pull origin feature/add-api-docs
  git merge feature/add-api-docs
  git push origin main
  
  # Teammate reviews your PR → Merge
  Same process
```

---

## 🚨 Conflict Resolution

### If There's a Merge Conflict
```bash
# Pull the latest changes
git pull origin main

# You'll see conflict markers in files
# Edit the file and choose which changes to keep

# After resolving
git add .
git commit -m "Resolve merge conflict"
git push origin main
```

---

## 📝 Commit Message Best Practices

### Good Commit Messages
```
✅ "Add batch export to JSON format"
✅ "Fix visibility decoding bug for code 75-80"
✅ "Refactor export functions for CLI and API"
✅ "Add CORS support to API"
```

### Bad Commit Messages
```
❌ "fix"
❌ "update"
❌ "changes"
❌ "asdfgh"
```

### Format
```
[Type] Short description (50 chars or less)

Longer explanation if needed (optional)
- Bullet point 1
- Bullet point 2

Types: Feature, Fix, Refactor, Docs, Test, Chore
```

---

## 🔐 SSH Setup (Optional, More Secure)

### Instead of HTTPS, use SSH:
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Add to GitHub Settings → SSH and GPG keys

# Use SSH URL instead of HTTPS
git remote set-url origin git@github.com:YOUR_USERNAME/synop-decoder.git
```

---

## 📱 GitHub Desktop (GUI Alternative)

If you prefer not to use command line:
1. Download: https://desktop.github.com/
2. Sign in with GitHub account
3. Clone repository
4. Make changes, commit, and push from GUI

---

## ✅ Quick Checklist for First Push

- [ ] Git installed on your computer
- [ ] Git configured with your name & email
- [ ] .gitignore file created
- [ ] Files staged: `git add .`
- [ ] Initial commit: `git commit -m "Initial commit"`
- [ ] Remote added: `git remote add origin https://...`
- [ ] Pushed to GitHub: `git push -u origin main`
- [ ] Teammate invited as collaborator
- [ ] Teammate cloned the repo

---

## 🆘 Need Help?

### Common Issues

**Q: How to undo the last commit?**
```bash
git reset HEAD~1
```

**Q: How to see what I changed?**
```bash
git diff

# Or in GitHub Desktop
```

**Q: Teammate has new changes, I don't see them?**
```bash
git pull origin main
```

**Q: Accidentally committed sensitive data?**
```bash
git filter-branch --tree-filter 'rm -f .env' HEAD
```

**Q: Want to start over?**
```bash
rm -rf .git
git init
git add .
git commit -m "Fresh start"
```

---

## 📚 Resources

- **Git Documentation:** https://git-scm.com/doc
- **GitHub Guides:** https://guides.github.com/
- **Branching Strategy:** https://git-flow.readthedocs.io/
- **Commit Guidelines:** https://www.conventionalcommits.org/

---

## 🎯 Next Steps

1. ✅ Follow "Initial Setup" section
2. ✅ Follow "Push to GitHub" section
3. ✅ Invite teammate as collaborator
4. ✅ Share this guide with teammate
5. ✅ Start collaborating using branching strategy

**Happy collaborating!** 🚀
