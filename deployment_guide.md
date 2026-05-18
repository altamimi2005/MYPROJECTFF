# SolarVision AI Deployment Guide

This guide will help you host your Solar Panel Classifier on **Render.com** so anyone can use it via a public link.

## Prerequisites
1.  A [GitHub](https://github.com/) account.
2.  A [Render](https://render.com/) account (linked to GitHub).

---

## Step 1: Upload to GitHub

You need to push your code (excluding the massive dataset) to GitHub.

1.  Open **Git Bash** (or any terminal) in your `MYPROJECT` folder.
2.  Initialize the repository:
    ```bash
    git init
    git branch -M main
    ```
3.  Add your files (Note: `.dockerignore` and `.gitignore` will automatically skip the huge dataset folders):
    ```bash
    git add .
    git commit -m "Deployment ready version"
    ```
4.  Create a new **Private** or Public repository on GitHub.
5.  Link and Push (Replace `YOUR_USERNAME` and `YOUR_REPO`):
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
    git push -u origin main
    ```

---

## Step 2: Deploy on Render

1.  Log in to [Render Dashboard](https://dashboard.render.com/).
2.  Click **"New +"** and select **"Web Service"**.
3.  Select **"Build and deploy from a Git repository"**.
4.  Connect your GitHub repository.
5.  **Settings**:
    *   **Name**: `solarvision-ai` (or anything you like)
    *   **Region**: Select the one closest to you.
    *   **Runtime**: **Docker** (Crucial: Select Docker, not Python).
    *   **Plan**: The "Free" tier works, but "Starter" ($7/mo) is recommended for smoother AI performance.
6.  Click **"Create Web Service"**.

---

## Step 3: Wait and Launch

Render will now:
1.  Download your code from GitHub.
2.  Build your Docker container (this will take 3-6 minutes).
3.  Provide you with a URL like `https://solarvision-ai.onrender.com`.

### Important Notes
*   **Memory Usage**: TensorFlow is memory-heavy. If the build fails with an "Out of Memory" error, you may need to upgrade to Render's "Starter" plan ($7/mo) which provides more RAM.
*   **Cold Start**: On the free plan, the web service will "sleep" after 15 minutes of inactivity. The first person to visit the site after it sleeps might wait 30 seconds for it to start up again.
