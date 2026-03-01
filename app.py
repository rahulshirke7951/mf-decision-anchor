import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# --- SETTINGS ---
FROZEN_START = "01-01-2023"

st.set_page_config(page_title="MF Anchor 2023", layout="wide")

# Sidebar for Inputs
st.sidebar.header("Navigation")
as_on_date = st.sidebar.date_input("Analysis Date (2026)", value=datetime.now())
codes_raw = st.sidebar.text_area("Scheme Codes (One per line)", "120465\n118989")
codes = [c.strip() for c in codes_raw.split("\n") if c.strip()]

@st.cache_data(ttl=3600)
def get_data(code):
    try:
        url = f"https://api.mfapi.in/mf/{code}?startDate={FROZEN_START}"
        data = requests.get(url).json()
        df = pd.DataFrame(data['data'])
        df['nav'] = df['nav'].astype(float)
        df['date'] = pd.to_datetime(df['date'], dayfirst=True)
        # Filter for the specific 'As On' date
        df = df[df['date'] <= pd.to_datetime(as_on_date)].sort_values('date')
        return data['meta']['scheme_name'], df
    except: return None, None

# Main Logic
st.title(f"⚓ MF Decision Anchor (Fixed: {FROZEN_START})")
stats = []

for c in codes:
    name, df = get_data(c)
    if name and not df.empty:
        # Growth Math
        ret = ((df['nav'].iloc[-1] - df['nav'].iloc[0]) / df['nav'].iloc[0]) * 100
        vol = df['nav'].pct_change().std() * np.sqrt(252) * 100
        stats.append({"Scheme": name, "Return %": round(ret, 2), "Volatility": round(vol, 2)})

if stats:
    st.table(pd.DataFrame(stats))
