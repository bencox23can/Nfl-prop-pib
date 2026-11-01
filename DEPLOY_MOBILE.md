# Launch NFL Prop Lab on your phone

## Option 1: Phone browser on the same Wi-Fi (no hosting account)
1. On your **Windows computer**, unzip the project and double-click `START_MOBILE_ON_WIFI.bat`.
2. On first run, allow Python through the Windows firewall for **private networks only** if prompted. Keep the terminal window open.
3. Find your PC's local IPv4 address from `ipconfig` (usually `192.168.x.x` or `10.x.x.x`).
4. On your Android or iPhone, connected to the **same Wi-Fi**, open `http://YOUR-PC-IP:8501` in Chrome or Safari. Replace YOUR-PC-IP with the actual number (no extra spaces).
5. Use your browser menu > **Add to Home screen** for one-tap access afterward.

**Important:** The PC must remain on and running; this mode does *not* run the Python server on the phone. LAN addresses are not public. If connectivity fails, check the firewall and Wi-Fi client isolation; do not expose port 8501 directly to the internet.

## Option 2: Access from your phone anywhere (cloud deployment)
1. Create a private or public GitHub repository with the `nfl_prop_lab` folder contents at the repository root, including `app.py`, `model.py`, `sources.py`, `requirements.txt`, and `data/`.
2. Sign in at https://share.streamlit.io/ and deploy a new app pointing to `app.py` in that repository.
3. Open the hosted Streamlit URL in your phone browser, then use **Add to Home screen**.
4. For live data, enter your odds API key in the app input. The app does not save it in its source files, but be mindful of hosted-app logs and provider quotas; configure secure app secrets for production deployments.

**Privacy and cost:** A hosted app sends uploaded CSV files to the hosting server. Check hosting pricing, visibility, usage limits, and data policy before uploading private data. Live odds require a suitable provider subscription. This package is ready for deployment but **has not been deployed** by the assistant.

## Limitations
The player projections are uncalibrated and not backtested. Manual matchup sliders apply to every player. The packaged demo is fictional. Mobile layout does not change the statistical validity of projections.
