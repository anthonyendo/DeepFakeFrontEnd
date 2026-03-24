# Home.py
# Main page — builds the UI and calls detectors.run_analysis() for results.

import streamlit as st

from styles import inject_custom_css
from layout import (
    render_settings,
    render_header,
    render_uploader,
    render_preview_and_options,
    render_results,
    render_history,
    render_footer,
)
from detectors import run_analysis

st.set_page_config(
    page_title="AI Deepfake Detector",
    page_icon="",
    layout="wide",
    menu_items={"About": "AI Deepfake Detector"},
)

inject_custom_css()

render_header()

with st.container(border=True):
    modality, use_remote, api_url = render_settings()
    uploader = render_uploader(modality)

render_preview_and_options(uploader, modality, use_remote, api_url)

st.write("")
go = st.button("Analyze", type="primary", use_container_width=True)

if "history" not in st.session_state:
    st.session_state.history = []

result = None

if go:
    result = run_analysis(uploader, modality, use_remote, api_url)

    if result and uploader:
        prob = float(result.get("probability", 0.0))
        label = result.get("label", "unknown")
        st.session_state.history.append(
            {"name": uploader.name, "mode": modality, "label": label, "prob": prob}
        )

render_results(result, uploader, modality)

render_history()

render_footer()
