# GitHub Upload Guide

> Step-by-step instructions to push your Credit Card Eligibility Prediction project to GitHub.

---

## Prerequisites

- A free GitHub account at [github.com](https://github.com)
- Git installed on your computer — download from [git-scm.com](https://git-scm.com/downloads)
- VS Code (optional but recommended) — [code.visualstudio.com](https://code.visualstudio.com)

---

## Step 1 — Create a New GitHub Repository

1. Go to [https://github.com](https://github.com) and log in.
2. Click the **+** icon (top-right) → **New repository**.
3. Fill in:
   - **Repository name:** `credit-eligibility-prediction`
   - **Description:** `ML-powered Credit Card Eligibility Prediction — FastAPI + MySQL`
   - **Visibility:** Public (required for Render free tier) or Private.
   - ❌ Do NOT initialize with README, .gitignore or license (we already have them).
4. Click **Create repository**.
5. Copy the repository URL shown — it will look like:
   ```
   https://github.com/YOUR_USERNAME/credit-eligibility-prediction.git
   ```

---

## Step 2 — Extract the ZIP

1. Right-click the downloaded ZIP file.
2. Select **Extract All…** → choose a folder (e.g., `C:\Projects\`).
3. You should see a folder named `credit_eligibility_project` with all project files inside.

---

## Step 3 — Open in VS Code

```bash
code "C:\Projects\credit_eligibility_project"
```

Or: open VS Code → **File** → **Open Folder…** → select `credit_eligibility_project`.

---

## Step 4 — Open the Integrated Terminal

In VS Code: **Terminal** → **New Terminal**

Confirm you are inside the project folder:
```bash
pwd          # Mac/Linux
cd           # Windows (shows current directory)
```
Expected output ends with `credit_eligibility_project`.

---

## Step 5 — Initialize Git

```bash
git init
```

---

## Step 6 — Configure Git Identity (first time only)

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

## Step 7 — Verify .env is NOT tracked

The `.gitignore` already excludes `.env`. Confirm:
```bash
cat .gitignore | grep ".env"
```
You should see `.env` listed. Never stage or commit `.env`.

---

## Step 8 — Add Files

```bash
git add .
```

Check what will be committed:
```bash
git status
```
You should see all project files listed in green. Confirm `.env` is **not** listed.

---

## Step 9 — Commit

```bash
git commit -m "Initial commit: Credit Card Eligibility Prediction — FastAPI + MySQL + ML"
```

---

## Step 10 — Connect to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/credit-eligibility-prediction.git
```
Replace `YOUR_USERNAME` with your actual GitHub username.

---

## Step 11 — Push to GitHub

```bash
git branch -M main
git push -u origin main
```

You will be prompted for your GitHub credentials.
> 💡 If password login fails, generate a **Personal Access Token** at:
> https://github.com/settings/tokens → Generate new token (classic) → tick **repo** scope.
> Use the token as your password.

---

## Step 12 — Verify on GitHub

1. Refresh your GitHub repository page.
2. You should see all files:
   - `backend/main.py`
   - `frontend/index.html`
   - `model/model_package.joblib`
   - `database/database.sql`
   - `requirements.txt`
   - `render.yaml`
   - `README.md`

---

## Important Security Reminders

| ✅ DO | ❌ DO NOT |
|---|---|
| Commit `.env.example` | Commit `.env` |
| Commit `database.sql` (schema) | Commit SQL data dumps with customer PII |
| Keep model file in `model/` | Hardcode database passwords |

---

## Updating the Repository Later

```bash
git add .
git commit -m "Update: describe what changed"
git push
```
