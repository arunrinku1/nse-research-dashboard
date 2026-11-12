# NSE Equity Research Desk — Simple Light English Edition

## Features
- Simple English navigation and step-by-step Help
- Light theme and responsive layout for mobile and desktop browsers
- Import one or multiple CSV files, including ZIP archives containing CSV files
- Stock search, historical comparison, technical indicators and data coverage audit
- Download cleaned history and latest-close reports

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run: `pip install -r requirements.txt`
4. Run: `streamlit run app.py`

## Deploy online
Upload this folder to a GitHub repository, then create a Streamlit Community Cloud app using `app.py` as the entry point. The `.streamlit/config.toml` file sets the light theme.

## Important limitations
- No full NSE historical dataset is bundled.
- Data must be uploaded by the user.
- Uploaded data stays in the current app session; it may need to be uploaded again after a refresh or a new session.
- The app is not a live intraday feed and does not place trades.
- Historical comparisons depend on complete, correctly adjusted data. This app cannot independently verify all corporate actions or missing sessions.
- Educational research only; not investment advice.
