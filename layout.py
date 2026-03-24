# layout.py
# UI components for the deepfake detector.
# Home.py calls these functions to build the page.

import base64
import json
from pathlib import Path
import os
import streamlit as st
import streamlit.components.v1 as components


def _get_api_url() -> str:
    """Get the backend API URL (used in remote mode only)."""
    try:
        return st.secrets["DEEFAKE_API_URL"]
    except Exception:
        return os.getenv("DEEFAKE_API_URL", "http://localhost:8000")


# ── Interactive waveform HTML/JS component ────────────────────────────

def _build_waveform_html(
    waveform_data: dict,
    markers: list,
    audio_b64: str,
    audio_mime: str,
    height: int = 160,
) -> str:
    """Return a self-contained HTML string with an interactive waveform player.

    - White bars for clean audio, red bars for fake-flagged segments.
    - Already-played portion darkens to a muted shade.
    - Play/pause button on the far left.
    """
    env_max = json.dumps(waveform_data["envelope_max"])
    env_min = json.dumps(waveform_data["envelope_min"])
    duration = waveform_data["duration"]
    fake_ranges = json.dumps([
        [m["start_sec"], m["end_sec"]]
        for m in markers if m.get("marked")
    ])

    return f"""
<div id="wf-wrap" style="display:flex;align-items:center;gap:10px;
     background:#0e1117;border-radius:10px;padding:8px 12px;">
  <button id="wf-play" style="
    width:40px;height:40px;border-radius:50%;border:2px solid #fff;
    background:transparent;color:#fff;font-size:18px;cursor:pointer;
    display:flex;align-items:center;justify-content:center;flex-shrink:0;
  ">&#9654;</button>
  <canvas id="wf-canvas" style="flex:1;height:{height}px;border-radius:6px;"></canvas>
</div>
<audio id="wf-audio" preload="auto" src="data:{audio_mime};base64,{audio_b64}"></audio>
<script>
(function() {{
  const envMax = {env_max};
  const envMin = {env_min};
  const duration = {duration};
  const fakeRanges = {fake_ranges};
  const N = envMax.length;

  const canvas = document.getElementById('wf-canvas');
  const ctx = canvas.getContext('2d');
  const audio = document.getElementById('wf-audio');
  const btn = document.getElementById('wf-play');

  function isFake(t) {{
    for (const [s, e] of fakeRanges) {{ if (t >= s && t <= e) return true; }}
    return false;
  }}

  function resize() {{
    const r = canvas.parentElement.getBoundingClientRect();
    canvas.width = canvas.clientWidth * (window.devicePixelRatio || 1);
    canvas.height = canvas.clientHeight * (window.devicePixelRatio || 1);
    ctx.setTransform(window.devicePixelRatio || 1, 0, 0,
                     window.devicePixelRatio || 1, 0, 0);
  }}

  function draw() {{
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    const mid = h / 2;
    const barW = Math.max(1, w / N);
    const curTime = audio.currentTime || 0;

    ctx.clearRect(0, 0, w, h);

    for (let i = 0; i < N; i++) {{
      const t = (i / N) * duration;
      const played = t <= curTime;
      const fake = isFake(t);

      let color;
      if (played && fake) color = '#7f1d1d';
      else if (played) color = '#444444';
      else if (fake) color = '#ef4444';
      else color = '#ffffff';

      const top = mid - (envMax[i] * mid);
      const bot = mid - (envMin[i] * mid);
      const barH = Math.max(1, bot - top);

      ctx.fillStyle = color;
      ctx.fillRect(i * barW, top, Math.ceil(barW) - 0.5, barH);
    }}

    requestAnimationFrame(draw);
  }}

  btn.addEventListener('click', function() {{
    if (audio.paused) {{
      audio.play();
      btn.innerHTML = '&#9646;&#9646;';
    }} else {{
      audio.pause();
      btn.innerHTML = '&#9654;';
    }}
  }});

  audio.addEventListener('ended', function() {{
    btn.innerHTML = '&#9654;';
  }});

  canvas.addEventListener('click', function(e) {{
    const rect = canvas.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    audio.currentTime = pct * duration;
    if (audio.paused) {{ audio.play(); btn.innerHTML = '&#9646;&#9646;'; }}
  }});

  resize();
  window.addEventListener('resize', resize);
  draw();
}})();
</script>
"""


def _build_video_waveform_html(
    waveform_data: dict,
    markers: list,
    video_b64: str,
    video_mime: str,
    height: int = 160,
) -> str:
    """HTML component: playable video on top, synced waveform below.

    The waveform darkens as the video plays.  Clicking the waveform seeks.
    """
    env_max = json.dumps(waveform_data["envelope_max"])
    env_min = json.dumps(waveform_data["envelope_min"])
    duration = waveform_data["duration"]
    fake_ranges = json.dumps([
        [m["start_sec"], m["end_sec"]]
        for m in markers if m.get("marked")
    ])

    return f"""
<div style="background:#0e1117;border-radius:10px;padding:10px;">
  <video id="vf-video" controls style="width:100%;border-radius:8px;display:block;"
         preload="auto" src="data:{video_mime};base64,{video_b64}"></video>
  <div style="display:flex;align-items:center;gap:10px;margin-top:8px;">
    <canvas id="vf-canvas" style="flex:1;height:{height}px;border-radius:6px;"></canvas>
  </div>
</div>
<script>
(function() {{
  const envMax = {env_max};
  const envMin = {env_min};
  const duration = {duration};
  const fakeRanges = {fake_ranges};
  const N = envMax.length;

  const canvas = document.getElementById('vf-canvas');
  const ctx = canvas.getContext('2d');
  const video = document.getElementById('vf-video');

  function isFake(t) {{
    for (const [s, e] of fakeRanges) {{ if (t >= s && t <= e) return true; }}
    return false;
  }}

  function resize() {{
    canvas.width = canvas.clientWidth * (window.devicePixelRatio || 1);
    canvas.height = canvas.clientHeight * (window.devicePixelRatio || 1);
    ctx.setTransform(window.devicePixelRatio || 1, 0, 0,
                     window.devicePixelRatio || 1, 0, 0);
  }}

  function draw() {{
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    const mid = h / 2;
    const barW = Math.max(1, w / N);
    const curTime = video.currentTime || 0;

    ctx.clearRect(0, 0, w, h);

    for (let i = 0; i < N; i++) {{
      const t = (i / N) * duration;
      const played = t <= curTime;
      const fake = isFake(t);

      let color;
      if (played && fake) color = '#7f1d1d';
      else if (played) color = '#444444';
      else if (fake) color = '#ef4444';
      else color = '#ffffff';

      const top = mid - (envMax[i] * mid);
      const bot = mid - (envMin[i] * mid);
      const barH = Math.max(1, bot - top);

      ctx.fillStyle = color;
      ctx.fillRect(i * barW, top, Math.ceil(barW) - 0.5, barH);
    }}

    requestAnimationFrame(draw);
  }}

  canvas.addEventListener('click', function(e) {{
    const rect = canvas.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    video.currentTime = pct * duration;
    if (video.paused) video.play();
  }});

  resize();
  window.addEventListener('resize', resize);
  draw();
}})();
</script>
"""


def _audio_b64(uploader) -> tuple[str, str]:
    """Return (base64_string, mime_type) from a Streamlit uploader object."""
    raw = uploader.getvalue()
    b64 = base64.b64encode(raw).decode("ascii")
    ext = Path(uploader.name).suffix.lower()
    mime_map = {
        ".wav": "audio/wav", ".mp3": "audio/mpeg", ".ogg": "audio/ogg",
        ".flac": "audio/flac", ".m4a": "audio/mp4",
    }
    mime = mime_map.get(ext, "audio/wav")
    return b64, mime


def _video_b64(uploader) -> tuple[str, str]:
    """Return (base64_string, mime_type) from a Streamlit uploader object."""
    raw = uploader.getvalue()
    b64 = base64.b64encode(raw).decode("ascii")
    ext = Path(uploader.name).suffix.lower()
    mime_map = {
        ".mp4": "video/mp4", ".mov": "video/quicktime", ".m4v": "video/mp4",
        ".avi": "video/x-msvideo", ".mkv": "video/x-matroska",
        ".webm": "video/webm",
    }
    mime = mime_map.get(ext, "video/mp4")
    return b64, mime


# ── Standard layout functions ─────────────────────────────────────────

def render_settings():
    """Draw the Settings area.

    Returns:
        modality, use_remote, api_url
    """
    st.markdown("### Settings")
    col1, col2 = st.columns([1, 2])

    with col1:
        modality = st.selectbox(
            "Input type", ["image", "video", "audio"], key="modality_select",
        )

    with col2:
        default_url = _get_api_url()

        if "use_remote_state" not in st.session_state:
            st.session_state.use_remote_state = False

        if st.session_state.use_remote_state:
            st.text_input("API URL", value=default_url, key="api_url_input")
        else:
            st.text_input("API URL", value=default_url, disabled=True,
                          key="api_url_disabled")

        use_remote = st.toggle(
            "Use remote API", value=st.session_state.use_remote_state,
            key="use_remote_toggle",
            help="OFF = run model locally | ON = call FastAPI backend",
        )
        st.session_state.use_remote_state = use_remote
        api_url = (
            st.session_state.get("api_url_input", default_url)
            if use_remote else default_url
        )

    st.divider()
    return modality, use_remote, api_url


def render_header():
    col_title, _ = st.columns([1, 0.25])
    with col_title:
        st.title("AI Deepfake Detector")
        st.caption("Upload an image, video, or audio clip to check if it is real or fake.")
    st.write("")


def render_uploader(modality: str):
    ACCEPT = {
        "image": ["jpg", "jpeg", "png"],
        "video": ["mp4", "mov", "m4v", "avi", "mkv"],
        "audio": ["wav", "mp3", "m4a", "flac", "ogg"],
    }
    return st.file_uploader(
        "Drag & drop a file or click to browse",
        type=ACCEPT[modality], accept_multiple_files=False,
        label_visibility="collapsed",
        help=f"Accepted: {', '.join(ACCEPT[modality])}",
    )


def render_preview_and_options(uploader, modality: str, use_remote: bool, api_url: str):
    with st.container():
        preview_cols = st.columns([1, 1], vertical_alignment="top")

        with preview_cols[0]:
            st.markdown("#### Preview")
            box = st.container(border=True)
            if uploader:
                if modality == "image":
                    with box: st.image(uploader, use_container_width=True)
                elif modality == "video":
                    with box: st.video(uploader)
                elif modality == "audio":
                    with box: st.audio(uploader)
            else:
                with box: st.info("No file uploaded yet", icon="📂")

        with preview_cols[1]:
            st.markdown("#### Options")
            with st.container(border=True):
                st.write("• **Mode:**", modality.title())
                if use_remote:
                    st.write("• **Backend:**", api_url)
                else:
                    st.write("• **Backend:** Local model")


# ── Results rendering ─────────────────────────────────────────────────

def render_results(result: dict | None, uploader, modality: str):
    if not result:
        return

    prob = float(result.get("probability", 0.0))
    label = result.get("label", "unknown")
    pct = f"{prob * 100:.1f}%"

    st.markdown("### Results")
    res_cols = st.columns([1, 1, 1.2])

    with res_cols[0]:
        st.metric("Deepfake probability", pct)
        st.progress(min(1.0, prob))

    with res_cols[1]:
        chip_class = "chip-fake" if label == "deepfake" else "chip-real"
        st.markdown(
            f'<span class="chip {chip_class}">{label.upper()}</span>',
            unsafe_allow_html=True,
        )
        st.caption("Decision threshold: 0.50")

    with res_cols[2]:
        if uploader:
            st.write("**File:**", uploader.name)
        else:
            st.write("**File:** —")
        st.write("**Mode:**", modality.title())

    annotated_img = result.get("annotated_image")
    waveform_data = result.get("waveform_data")
    audio_markers = result.get("markers", [])
    fake_audio = [m for m in audio_markers if m.get("marked")]

    # ── Image: annotated image with circle overlays, no pixel text ──
    if modality == "image":
        if annotated_img is not None:
            st.image(annotated_img, use_container_width=True)

    # ── Audio: interactive waveform player ──────────────────────────
    if modality == "audio":
        if waveform_data and uploader:
            b64, mime = _audio_b64(uploader)
            html = _build_waveform_html(waveform_data, audio_markers, b64, mime)
            components.html(html, height=200)
            st.caption("White = clean  •  Red = fake  •  Darker = already played")

        if fake_audio:
            st.warning(
                f"{len(fake_audio)} of {len(audio_markers)} segments flagged.",
                icon="🔴",
            )
        elif audio_markers:
            st.success("No segments flagged as fake.", icon="✅")

    # ── Video: annotated frame (stacked) + playable video with synced waveform ──
    if modality == "video":
        if annotated_img is not None:
            st.markdown("#### Frame Analysis")
            st.image(annotated_img, use_container_width=True)

        if waveform_data and uploader:
            st.markdown("#### Video + Audio Timeline")
            b64, mime = _video_b64(uploader)
            html = _build_video_waveform_html(
                waveform_data, audio_markers, b64, mime,
            )
            components.html(html, height=500)
            st.caption("White = clean  •  Red = fake  •  Darker = already played")

        if fake_audio:
            st.warning(
                f"{len(fake_audio)} of {len(audio_markers)} audio segments flagged.",
                icon="🔴",
            )
        elif audio_markers:
            st.success("No audio segments flagged as fake.", icon="✅")


def render_history():
    history = st.session_state.get("history", [])
    if not history:
        return

    st.markdown("### Recent Analyses")
    hist_cols = st.columns([2, 1, 1, 1])
    hist_cols[0].markdown("**File**")
    hist_cols[1].markdown("**Type**")
    hist_cols[2].markdown("**Result**")
    hist_cols[3].markdown("**Prob.**")

    for row in reversed(history[-7:]):
        c0, c1, c2, c3 = st.columns([2, 1, 1, 1])
        c0.write(row["name"])
        c1.write(row["mode"])
        chip_class = "chip-fake" if row["label"] == "deepfake" else "chip-real"
        c2.markdown(
            f'<span class="chip {chip_class}">{row["label"]}</span>',
            unsafe_allow_html=True,
        )
        c3.write(f"{row['prob'] * 100:.1f}%")


def render_footer():
    st.markdown(
        """
<div class="footer">
<b>Notes</b>: Results are produced by the Xception (image) and AudioClassifier (audio) models
trained on data from the S3 deepfake dataset.
</div>
""",
        unsafe_allow_html=True,
    )
