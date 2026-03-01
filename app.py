import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURATION ---
FROZEN_START = "01-01-2023"

st.set_page_config(page_title="MF Universal Anchor", layout="wide")

@st.cache_data(ttl=86400)
def get_master_list():
    # Fetches all ~13,000 schemes available in the API
    return requests.get("https://api.mfapi.in/mf").json()

def get_asset_class(name):
    name = name.upper()
    if any(x in name for x in ["GOLD", "SILVER", "METAL"]): return "Metals (Gold/Silver)"
    if "ETF" in name: return "ETFs"
    if any(x in name for x in ["GILT", "G-SEC", "GOVERNMENT"]): return "G-Sec / Gilt"
    if "SMALL CAP" in name: return "Small Cap"
    if "MID CAP" in name: return "Mid Cap"
    if "FLEXI CAP" in name: return "Flexi Cap"
    if "BLUECHIP" in name or "LARGE CAP" in name: return "Large Cap"
    return "Other Equity/Debt"

# --- SIDEBAR ---
st.sidebar.header("Universal Explorer")
as_on_date = st.sidebar.date_input("Analysis Date", value=datetime.now())
target_asset = st.sidebar.selectbox("Select Category to Load", 
    ["Small Cap", "Mid Cap", "Metals (Gold/Silver)", "ETFs", "G-Sec / Gilt", "Large Cap"])

# --- DATA ENGINE ---
master_list = get_master_list()
# Filter master list by the chosen category and "Growth"
filtered_schemes = [s for s in master_list 
                   if target_asset in get_asset_class(s['schemeName']) 
                   and "GROWTH" in s['schemeName'].upper()]

st.title(f"🚀 {target_asset} Universe")
st.caption(f"Showing all Growth schemes found in {target_asset} (Fixed Start: Jan 2023)")

if st.button(f"Analyze all {len(filtered_schemes)} {target_asset} Funds"):
    results = []
    progress_bar = st.progress(0)
    
    # We limit to top 20 for speed in the demo, but you can remove the [:20]
    for i, s in enumerate(filtered_schemes[:20]): 
        try:
            code = s['schemeCode']
            url = f"https://api.mfapi.in/mf/{code}?startDate={FROZEN_START}"
            resp = requests.get(url).json()
            df = pd.DataFrame(resp['data'])
            df['nav'] = df['nav'].astype(float)
            df['date'] = pd.to_datetime(df['date'], dayfirst=True)
            df = df[df['date'] <= pd.to_datetime(as_on_date)].sort_values('date')
            
            if not df.empty:
                ret = ((df['nav'].iloc[-1] - df['nav'].iloc[0]) / df['nav'].iloc[0]) * 100
                results.append({
                    "AMC": resp['meta']['amc_name'],
                    "Scheme": resp['meta']['scheme_name'],
                    "Return %": round(ret, 2),
                    "Latest NAV": df['nav'].iloc[-1]
                })
        except: continue
        progress_bar.progress((i + 1) / 20)

    if results:
        res_df = pd.DataFrame(results)
        
        # Display by AMC Grouping
        for amc, group in res_df.groupby("AMC"):
            with st.expander(f"🏢 {amc}"):
                st.table(group[["Scheme", "Return %", "Latest NAV"]])
