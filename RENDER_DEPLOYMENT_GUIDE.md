# 🚀 Deploying QA Agent to Render

Render is a cloud platform that makes it incredibly easy to host Dockerized web applications. Since we already have a production-ready `Dockerfile`, deploying the QA Agent Streamlit app will take about 5 minutes.

Here is the exact step-by-step process:

## Prerequisites
1. Ensure your latest code is pushed to your **GitHub** repository.
2. Ensure you have the `Dockerfile` in the root of your repository (it has already been configured for Render).

---

## Step 1: Create a Render Account
1. Go to [Render.com](https://render.com) and sign up using your GitHub account.

## Step 2: Create a New Web Service
1. Once logged in, click the **"New +"** button in the top right corner.
2. Select **"Web Service"**.
3. Select **"Build and deploy from a Git repository"** and click **Next**.
4. Connect your GitHub account (if not already connected) and select the `sg-qa-agent` repository.

## Step 3: Configure the Web Service
Render will automatically detect the `Dockerfile`, but verify the settings:

* **Name:** `sg-qa-agent` (or whatever you prefer)
* **Region:** Choose the region closest to your agency (e.g., `Oregon (US West)` or `Frankfurt (EU)`).
* **Branch:** `main` (or the branch you are using)
* **Environment:** Ensure it says **`Docker`**.
* **Instance Type:** Select **Free** (or a paid tier if you expect heavy usage, as Playwright browser testing requires some memory). 

> [!WARNING]
> Because Playwright loads a full headless Chromium browser into memory for every scan, the Free tier (512MB RAM) *might* occasionally run out of memory during very heavy/complex website scans. If this happens, you should upgrade to the **Starter** instance type ($7/month, 512MB RAM but no sleep) or **Standard** ($25/month, 2GB RAM).

## Step 4: Add Environment Variables
Scroll down and click on **Environment Variables**:
1. Add a new variable:
   * **Key:** `PORT`
   * **Value:** `10000`
   *(Render dynamically assigns ports, but our Dockerfile is hardcoded to expose 10000. Setting this variable ensures Render routes traffic correctly to Streamlit).*

*(Note: We do **not** add the Asana token here, because the Quick Start UI now asks users to paste their token directly and securely in the browser).*

## Step 5: Deploy!
1. Click **Create Web Service** at the bottom of the page.
2. Render will now start building your Docker container. This process will take a few minutes as it downloads Python, installs Playwright, and downloads the Chromium browser.
3. You can watch the live terminal logs on the screen.

## Step 6: Access Your Live App
Once the logs say `Your service is live 🎉`, look at the top left of the dashboard. You will see a URL that looks something like:
`https://sg-qa-agent.onrender.com`

**Click that link!** You can now share this exact link with anyone on your team, and they can use the web interface immediately from their own laptops without installing any code.
