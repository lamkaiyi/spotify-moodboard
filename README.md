# Spotify Moodboard 🎵

An automated, self-refreshing Spotify Moodboard that displays your listening history and favorite playlists. 

Built using a **Static Site Generation** approach: a GitHub Action runs a Python script daily to fetch your Spotify data and directly inject it into an HTML template using Jinja2. This results in a blazing-fast, premium glassmorphic UI that requires zero client-side JavaScript for data fetching!

View my example here: https://lamkaiyi.github.io/spotify-moodboard/

## Features
- 🕒 **Recent Tracks**: See what you've been listening to recently.
- 🏆 **All-Time Top Tracks**: Show off your all-time favorite songs.
- 📂 **Your Playlists**: Display your public playlists.
- 💅 **Premium UI**: Vibrant dark mode, glassmorphism cards, hover micro-animations, and a silky smooth horizontal scrolling carousel powered purely by CSS Scroll Snap.
- 🤖 **Fully Automated**: Updates automatically every midnight via GitHub Actions.
- 💸 **100% Free**: Hosted on GitHub Pages.

---

## 🛠️ How to Replicate (Setup Guide)

Follow these steps to create your own personalized, self-updating Spotify Moodboard.

### Step 1: Fork or Clone this Repository
1. Fork this repository to your own GitHub account.
2. Clone it to your local machine (optional, but needed to run the token script).

### Step 2: Create a Spotify Developer App
1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) and log in.
2. Click **Create app**.
3. Give it a name and description.
4. For the **Redirect URI**, you MUST enter exactly: `https://example.com/callback`
5. Check the agreement box and click **Save**.
6. Go to the **Settings** of your new app to find your `Client ID` and `Client Secret`.

### Step 3: Get Your Refresh Token
You need to authenticate the app to read your personal Spotify data. We've included a helper script to make this painless.

1. Ensure you have Python installed, then install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the token generation script:
   ```bash
   python get_token.py
   ```
3. When prompted, paste your `Client ID` and `Client Secret`.
4. Your browser will open Spotify. Click **Agree** to authorize the app.
5. You will be redirected to `example.com`. **Copy the entire URL** from your browser's address bar (it will look like `https://example.com/callback?code=AQD...`).
6. Paste that full URL back into your terminal.
7. The script will print out your **Refresh Token**. Save this!

### Step 4: Configure GitHub Secrets
To allow the GitHub Action to run automatically, you need to provide it with your credentials securely.

1. Go to your repository on GitHub.
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret** and add the following three secrets exactly as written:
   - `SPOTIFY_CLIENT_ID` (Your Client ID)
   - `SPOTIFY_CLIENT_SECRET` (Your Client Secret)
   - `SPOTIFY_REFRESH_TOKEN` (The token you got in Step 3)

### Step 5: Enable GitHub Pages
1. Go to **Settings** > **Pages** in your GitHub repository.
2. Under "Build and deployment", set the **Source** to "Deploy from a branch".
3. Select the `main` (or `master`) branch and the `/ (root)` folder, then click **Save**.

### Step 6: Trigger the Initial Build!
1. Go to the **Actions** tab in your repository.
2. Click on the **Daily Refresh** workflow on the left sidebar.
3. Click the **Run workflow** dropdown on the right and hit the green button to trigger it manually.
4. Wait about 30 seconds for the action to complete. It will fetch your real Spotify data, generate the new `index.html`, and commit it to the repo.
5. Go to your GitHub Pages URL (e.g., `https://[your-username].github.io/[repo-name]`) to see your live moodboard!

---

## Local Development
If you want to tweak the CSS, HTML template, or test real data locally:
1. **With Dummy Data**: Just run `python generate_site.py`. If no credentials are set, the script will automatically fallback to generating **dummy data**.
2. **With Real Data (.env option)**: 
   - Create a copy of `.env.example` and name it `.env`.
   - Fill in your `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REFRESH_TOKEN` inside the `.env` file.
   - Run `python generate_site.py`. It will automatically load your credentials and fetch your real Spotify data.
3. Open `index.html` in your browser to view your design changes instantly!
