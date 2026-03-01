import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# --- SETTINGS ---
FROZEN_START = "01-01-2023"

st.set_page_config(page_title="MF Decision Anchor", layout="wide")

# Sidebar Controls
st.sidebar.header("⚓ Anchor Controls")
as_on_date = st.sidebar.date_input("Analysis Date", value=datetime.now())
codes_raw = st.sidebar.text_area("Enter Scheme Codes (One per line)", "120465\n118989\n148918\n145554")
codes = [c.strip() for c in codes_raw.split("\n") if c.strip()]

@st.cache_data(ttl=3600)
def fetch_full_data(code):
    try:
        url = f"https://api.mfapi.in/mf/{code}?startDate={FROZEN_START}"
        resp = requests.get(url).json()
        meta = resp['meta']
        
        # Determine Broad Asset Class for your "Metals/Gilt" requirement
        category = meta.get('scheme_category', 'Other')
        name = meta.get('scheme_name', '')
        
        # Custom Tagging Logic
        asset_tag = "Equity/Debt"
        if any(x in name.upper() for x in ["GOLD", "SILVER", "METALS"]): asset_tag = "Metals (Gold/Silver)"
        elif "ETF" in name.upper(): asset_tag = "ETFs"
        elif any(x in category.upper() for x in ["GILT", "G-SEC"]): asset_tag = "G-Sec / Gilt"
        elif "SMALL CAP" in category.upper(): asset_tag = "Small Cap"
        elif "MID CAP" in category.upper(): asset_tag = "Mid Cap"

        df = pd.DataFrame(resp['data'])
        df['nav'] = df['nav'].astype(float)
        df['date'] = pd.to_datetime(df['date'], dayfirst=True)
        df = df[df['date'] <= pd.to_datetime(as_on_date)].sort_values('date')
        
        return {
            "Code": code,
            "Scheme": name,
            "AMC": meta.get('amc_name'),
            "Category": asset_tag,
            "Raw_Category": category,
            "NAV": df['nav'].iloc[-1],
            "Return %": round(((df['nav'].iloc[-1] - df['nav'].iloc[0]) / df['nav'].iloc[0]) * 100, 2),
            "Volatility": round(df['nav'].pct_change().std() * np.sqrt(252) * 100, 2)
        }
    except: return None

# --- EXECUTION ---
all_results = []
for c in codes:
    res = fetch_full_data(c)
    if res: all_results.append(res)

if all_results:
    master_df = pd.DataFrame(all_results)

    # --- TABS FOR SUB-CATEGORIES ---
    tab1, tab2, tab3 = st.tabs(["📂 By Asset Class", "🏢 By AMC", "📊 Full Leaderboard"])

    with tab1:
        st.subheader("Sub-Category Breakdown")
        for asset, group in master_df.groupby("Category"):
            with st.expander(f"{asset} ({len(group)} funds)"):
                st.table(group[["Scheme", "Return %", "Volatility"]])

    with tab2:
        st.subheader("AMC Wise Analysis")
        selected_amc = st.selectbox("Select AMC", master_df["AMC"].unique())
        amc_data = master_df[master_df["AMC"] == selected_amc]
        st.dataframe(amc_data[["Scheme", "Category", "Return %"]], use_container_width=True)

    with tab3:
        st.subheader("Ranked Performance (Jan 2023 - Present)")
        st.dataframe(master_df.sort_values("Return %", ascending=False), use_container_width=True)
else:
    st.info("Paste codes in the sidebar to begin.")
