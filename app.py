"""
VPM Tools — Multi-tool Streamlit app

Run with:
  streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="VPM Tools",
    page_icon="📻",
    layout="centered",
)

st.title("📻 VPM Tools")
st.caption("Internal tools for the VPM web team.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/1_Megaphone.py", label="Megaphone Episode Duplicator", icon="🎙️")
    st.caption("Copy episodes between podcasts and networks.")

with col2:
    st.page_link("pages/2_Chartbeat.py", label="Chartbeat Analytics", icon="📊")
    st.caption("Weekly traffic dashboard from CSV exports.")
