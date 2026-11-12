import io
import zipfile
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="NSE Equity Research Desk",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root { color-scheme: light; }
.stApp { background: #F7F9FC; color: #172554; }
.block-container { max-width: 1320px; padding-top: 1.15rem; padding-bottom: 2rem; }
[data-testid="stHeader"] { background: rgba(247,249,252,.94); }
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E5EAF2; }
[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #E2E8F0; padding: 13px; border-radius: 13px; }
div[data-testid="stDataFrame"] { background: white; border-radius: 12px; }
div.stButton > button, div.stDownloadButton > button { border-radius: 9px; min-height: 2.6rem; }
div[data-testid="stFileUploader"] { background: #FFFFFF; border: 1px dashed #93C5FD; border-radius: 12px; padding: 10px; }
@media(max-width:700px) {
 .block-container { padding-left: .75rem; padding-right: .75rem; }
 [data-testid="stMetric"] { padding: 9px; }
}
</style>
""", unsafe_allow_html=True)

st.title("📊 NSE Equity Research Desk")
st.caption("Simple stock research dashboard • Mobile + Desktop • Educational use only, not investment advice")

TEMPLATE = """Date,Symbol,Open,High,Low,Close,Volume
2026-11-11,DEMO,100,105,99,104,250000
2026-11-12,DEMO,104,108,103,107,300000
"""

def normalize(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    aliases = {
        "trad_dt":"date", "timestamp":"date", "trade_date":"date",
        "tckr_symbol":"symbol", "ticker":"symbol",
        "opnpric":"open", "open_price":"open",
        "hghpric":"high", "high_price":"high",
        "lwpric":"low", "low_price":"low",
        "clspric":"close", "close_price":"close", "last_price":"close",
        "ttl_trd_qnty":"volume", "tottrdqty":"volume",
        "total_traded_quantity":"volume", "no_of_shrs":"volume"
    }
    df = df.rename(columns={c: aliases[c] for c in df.columns if c in aliases})
    required = ["date", "symbol", "open", "high", "low", "close"]
    if not all(c in df.columns for c in required):
        return None
    if "volume" not in df.columns:
        df["volume"] = np.nan
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", "", regex=False), errors="coerce")
    df = df.dropna(subset=["date", "symbol", "close"])
    return df[["date", "symbol", "open", "high", "low", "close", "volume"]]

def load_uploads(uploaded):
    frames, errors = [], []
    for f in uploaded or []:
        try:
            raw = f.getvalue()
            if f.name.lower().endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                    for name in zf.namelist():
                        if name.lower().endswith(".csv"):
                            try:
                                item = normalize(pd.read_csv(zf.open(name)))
                                if item is not None and len(item):
                                    frames.append(item)
                                else:
                                    errors.append(f"{name}: required columns were not found")
                            except Exception as exc:
                                errors.append(f"{name}: {exc}")
            else:
                item = normalize(pd.read_csv(io.BytesIO(raw)))
                if item is not None and len(item):
                    frames.append(item)
                else:
                    errors.append(f"{f.name}: required columns were not found")
        except Exception as exc:
            errors.append(f"{f.name}: {exc}")
    if not frames:
        return pd.DataFrame(), errors
    data = pd.concat(frames, ignore_index=True)
    data = data.drop_duplicates(["symbol", "date"], keep="last")
    return data.sort_values(["symbol", "date"]), errors

if "market_data" not in st.session_state:
    st.session_state.market_data = pd.DataFrame()
if "load_errors" not in st.session_state:
    st.session_state.load_errors = []

with st.sidebar:
    st.subheader("Navigation")
    page = st.radio(
        "Select a section",
        ["🏠 Home", "📥 Import Data", "🔎 Stock Search", "📈 Historical Analysis",
         "🧮 Technical Analysis", "🗂️ Data Coverage", "📄 Reports", "❓ Help"],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption("Data is kept in the current app session. You may need to upload it again after a refresh or a new session.")
    if st.button("Clear Uploaded Data", use_container_width=True):
        st.session_state.market_data = pd.DataFrame()
        st.session_state.load_errors = []
        st.rerun()

data = st.session_state.market_data
has_data = not data.empty

def need_data():
    if not has_data:
        st.info("Please open **Import Data** and upload a CSV or ZIP file first.")
        return False
    return True

if page == "🏠 Home":
    st.subheader("Research Home")
    if has_data:
        a, b, c = st.columns(3)
        a.metric("Companies", f"{data.symbol.nunique():,}")
        b.metric("Total Records", f"{len(data):,}")
        c.metric("Date Coverage", f"{data.date.min():%d %b %Y} – {data.date.max():%d %b %Y}")
        st.success("Your data is ready. Choose a section from the left menu.")
        st.subheader("Latest Available Data")
        latest = data.sort_values("date").groupby("symbol").tail(1).sort_values("symbol")
        st.dataframe(latest, use_container_width=True, hide_index=True)
    else:
        st.info("Follow these simple steps to get started.")
        st.markdown("""
        1. Open **Import Data**.
        2. Select NSE historical CSV files or a ZIP containing CSV files.
        3. After importing, use Stock Search or Historical Analysis.
        """)
        st.download_button("📄 Download Sample CSV", TEMPLATE.encode("utf-8"),
                           "sample_nse_history.csv", "text/csv")
    st.caption("This tool is for learning and historical data research. It does not provide buy/sell signals.")

elif page == "📥 Import Data":
    st.subheader("📥 Import Your Data")
    st.write("Select one or more CSV files. You can also upload a ZIP file containing multiple CSV files.")
    st.download_button("Download Sample CSV", TEMPLATE.encode("utf-8"),
                       "sample_nse_history.csv", "text/csv")
    uploaded = st.file_uploader("Choose CSV or ZIP files", type=["csv", "zip"], accept_multiple_files=True)
    if st.button("Load Data", type="primary", disabled=not uploaded):
        loaded, errs = load_uploads(uploaded)
        st.session_state.market_data = loaded
        st.session_state.load_errors = errs
        st.rerun()
    if has_data:
        st.success(f"{len(data):,} records loaded across {data.symbol.nunique():,} companies.")
    if st.session_state.load_errors:
        st.warning("Some files could not be read:")
        for msg in st.session_state.load_errors[:8]:
            st.write("• " + msg)
    with st.expander("Which columns are required?"):
        st.code("Date, Symbol, Open, High, Low, Close, Volume")
        st.caption("Date, NSE Symbol and OHLC prices are required. Volume is optional.")

elif page == "🔎 Stock Search":
    st.subheader("🔎 Search a Company / Symbol")
    if need_data():
        q = st.text_input("Enter an NSE Symbol", placeholder="e.g. RELIANCE, TCS, INFY")
        symbols = sorted(data.symbol.unique())
        matches = [s for s in symbols if q.strip().upper() in s] if q.strip() else symbols
        st.caption(f"{len(matches)} matching symbols")
        if matches:
            chosen = st.selectbox("Select a stock", matches)
            hist = data[data.symbol == chosen].sort_values("date")
            x, y, z = st.columns(3)
            x.metric("Latest Close", f"₹{hist.iloc[-1].close:,.2f}")
            y.metric("First Date", hist.date.min().strftime("%d-%b-%Y"))
            z.metric("Records", f"{len(hist):,}")
            st.line_chart(hist.set_index("date")[["close"]], use_container_width=True)
            st.dataframe(hist.tail(30), use_container_width=True, hide_index=True)
        else:
            st.warning("No matching symbol was found in the uploaded data.")

elif page == "📈 Historical Analysis":
    st.subheader("📈 Historical High Comparison")
    st.caption("This compares only the uploaded data. Incomplete or unadjusted history can change the result.")
    if need_data():
        chosen = st.selectbox("Select a stock", sorted(data.symbol.unique()))
        years = st.selectbox("Comparison period", [5, 10, 15, 20], index=0)
        hist = data[data.symbol == chosen].sort_values("date")
        latest = hist.iloc[-1]
        cutoff = latest.date - pd.DateOffset(years=years)
        window = hist[hist.date >= cutoff]
        if len(window) < 2:
            st.warning("There are not enough records for this period.")
        else:
            previous = window.iloc[:-1]
            prior_high = previous.high.max()
            a, b = st.columns(2)
            a.metric("Latest Close", f"₹{latest.close:,.2f}")
            b.metric(f"Previous {years}-Year High", f"₹{prior_high:,.2f}")
            st.write(f"Available comparison dates: **{window.date.min():%d-%b-%Y} to {previous.date.max():%d-%b-%Y}**")
            if latest.close > prior_high:
                st.success("The latest close is above the previous period high in the uploaded sample.")
            else:
                st.info("The latest close is not above the previous period high in the uploaded sample.")
            st.line_chart(window.set_index("date")[["close"]], use_container_width=True)

elif page == "🧮 Technical Analysis":
    st.subheader("🧮 Technical Indicators")
    if need_data():
        chosen = st.selectbox("Select a stock", sorted(data.symbol.unique()), key="tech_symbol")
        hist = data[data.symbol == chosen].sort_values("date").copy()
        hist["SMA 20"] = hist.close.rolling(20).mean()
        hist["SMA 50"] = hist.close.rolling(50).mean()
        hist["EMA 20"] = hist.close.ewm(span=20, adjust=False).mean()
        delta = hist.close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        hist["RSI 14"] = 100 - (100 / (1 + rs))
        fast = hist.close.ewm(span=12, adjust=False).mean()
        slow = hist.close.ewm(span=26, adjust=False).mean()
        hist["MACD"] = fast - slow
        st.line_chart(hist.set_index("date")[["close", "SMA 20", "SMA 50", "EMA 20"]].tail(250),
                      use_container_width=True)
        st.dataframe(hist[["date", "close", "SMA 20", "SMA 50", "EMA 20", "RSI 14", "MACD", "volume"]].tail(30),
                     use_container_width=True, hide_index=True)
        st.caption("Indicators are mathematical measures, not standalone decision rules.")

elif page == "🗂️ Data Coverage":
    st.subheader("🗂️ Data Coverage Check")
    if need_data():
        audit = data.groupby("symbol").agg(
            First_Date=("date", "min"), Last_Date=("date", "max"), Records=("date", "count")
        ).reset_index()
        audit["Calendar_Days"] = (audit["Last_Date"] - audit["First_Date"]).dt.days
        st.write("This table shows the date range covered by the uploaded records for each symbol.")
        st.dataframe(audit.sort_values("Calendar_Days"), use_container_width=True, hide_index=True)
        st.warning("This check does not independently verify corporate actions, bonus/split adjustments, symbol changes or missing trading sessions.")

elif page == "📄 Reports":
    st.subheader("📄 Download Reports")
    if need_data():
        st.write("Download a cleaned copy of the uploaded data.")
        csv_bytes = data.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Complete Cleaned History CSV", csv_bytes,
                           "nse_normalized_history.csv", "text/csv", use_container_width=True)
        latest = data.sort_values("date").groupby("symbol").tail(1).sort_values("symbol")
        st.download_button("⬇️ Download Latest Close Report", latest.to_csv(index=False).encode("utf-8"),
                           "nse_latest_close.csv", "text/csv", use_container_width=True)
        st.dataframe(latest, use_container_width=True, hide_index=True)

elif page == "❓ Help":
    st.subheader("❓ Quick Help")
    with st.expander("1. How do I import data?", expanded=True):
        st.write("Open Import Data → choose CSV/ZIP files → click Load Data.")
    with st.expander("2. How do I view a stock?"):
        st.write("Open Stock Search → enter a symbol → select the stock.")
    with st.expander("3. How do I compare 5–20 years?"):
        st.write("Open Historical Analysis → select a stock and period → review the available historical high.")
    with st.expander("4. How do I download reports?"):
        st.write("Open Reports and select the CSV download button.")
    with st.expander("5. Where can I get historical data?"):
        st.write("Use NSE official Historical Reports / All Reports where available. Check each file's date range and corporate-action adjustments.")
    st.caption("This app is not a live intraday feed. Complete historical data is not bundled; you must upload your CSV/ZIP files.")

st.divider()
st.caption("Educational research tool • No live intraday quotes • No investment advice • Always verify data quality and corporate-action adjustments")
