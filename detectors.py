"""
detectors.py

Connects the Streamlit UI to the deepfake detection models from the 490
project.  Supports three modalities: image, audio, video.

Entry point for the UI:

    run_analysis(uploader, modality, use_remote, api_url)

Two prediction modes:
  - LOCAL: loads the trained models directly (default)
  - REMOTE: calls the FastAPI backend over HTTP
"""

import os
import sys
import tempfile
from pathlib import Path

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Make the 490 project importable so we can call the models directly.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent / "490")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Lazy model loaders — cached so they only load once per Streamlit session.
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading image model…")
def _load_image_model():
    from deepfake_detector.scripts.infer_image import load_model, load_model_from_s3
    ckpt_dir = os.path.join(_PROJECT_ROOT, "deepfake_detector", "checkpoints", "image_check")
    candidates = sorted(
        [f for f in os.listdir(ckpt_dir) if f.endswith(".pt")]
    ) if os.path.isdir(ckpt_dir) else []
    if candidates:
        return load_model(os.path.join(ckpt_dir, candidates[-1]))
    return load_model_from_s3(local_dir=ckpt_dir)


@st.cache_resource(show_spinner="Loading audio model…")
def _load_audio_model():
    from deepfake_detector.scripts.audio_stub import load_audio_model
    ckpt_dir = os.path.join(_PROJECT_ROOT, "deepfake_detector", "checkpoints", "audio_check")
    return load_audio_model(ckpt_path=None)


# ---------------------------------------------------------------------------
# Local prediction — runs the model in-process, no HTTP server needed.
# ---------------------------------------------------------------------------

def local_predict(tmp_path: str, modality: str) -> dict | None:
    """Run the trained model directly on the uploaded file.

    Returns:
        dict with "label" ("deepfake" | "real") and "probability" (float),
        or None on failure.
    """
    try:
        if modality == "image":
            from deepfake_detector.scripts.infer_image import score_image
            from deepfake_detector.scripts.annotate_image import annotate
            model = _load_image_model()
            fused, detail = score_image(tmp_path, model)
            if fused is None:
                st.error("Could not score this image (no detections found).")
                return None

            annotated_img, markers = annotate(tmp_path, model)

            prob = float(fused)
            return {
                "label": "deepfake" if prob >= 0.5 else "real",
                "probability": round(prob, 4),
                "detail": detail,
                "annotated_image": annotated_img,
                "markers": markers,
            }

        elif modality == "audio":
            from deepfake_detector.scripts.audio_stub import score_audio
            from deepfake_detector.scripts.annotate_audio import (
                annotate_audio, get_waveform_envelope,
            )
            model = _load_audio_model()
            result = score_audio(tmp_path, model=model)
            if result is None:
                st.error(
                    "Could not process the audio file. "
                    "Make sure librosa, soundfile, and ffmpeg are installed."
                )
                return None

            markers = annotate_audio(tmp_path, model)
            waveform_data = get_waveform_envelope(tmp_path)

            prob = float(result.prob_fake)
            return {
                "label": "deepfake" if prob >= 0.5 else "real",
                "probability": round(prob, 4),
                "detail": result.detail,
                "markers": markers,
                "waveform_data": waveform_data,
            }

        elif modality == "video":
            from deepfake_detector.scripts.infer_video import score_video, extract_frames
            from deepfake_detector.scripts.annotate_image import annotate as annotate_frame
            from deepfake_detector.scripts.annotate_audio import (
                annotate_audio, get_waveform_envelope,
            )
            import cv2

            image_model = _load_image_model()
            try:
                audio_model = _load_audio_model()
            except Exception:
                audio_model = None

            fused, detail = score_video(
                tmp_path, image_model, audio_model=audio_model
            )
            if fused is None:
                st.error("Could not score this video (no valid frames).")
                return None

            annotated_frame = None
            image_markers = []
            frames = extract_frames(tmp_path, fps_sample=1, max_frames=8)
            if frames:
                pick = frames[len(frames) // 4] if len(frames) > 1 else frames[0]
                frame_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                cv2.imwrite(frame_tmp.name, pick)
                frame_tmp.close()
                try:
                    annotated_frame, image_markers = annotate_frame(
                        frame_tmp.name, image_model
                    )
                except Exception:
                    pass
                try:
                    os.unlink(frame_tmp.name)
                except Exception:
                    pass

            audio_markers = annotate_audio(tmp_path, audio_model) if audio_model else []
            waveform_data = get_waveform_envelope(tmp_path) if audio_model else None

            prob = float(fused)
            return {
                "label": "deepfake" if prob >= 0.5 else "real",
                "probability": round(prob, 4),
                "detail": detail,
                "annotated_image": annotated_frame,
                "image_markers": image_markers,
                "markers": audio_markers,
                "waveform_data": waveform_data,
            }

        else:
            st.error(f"Unknown modality: {modality}")
            return None

    except FileNotFoundError as e:
        st.error(f"Model checkpoint not found: {e}")
        st.caption(
            "Make sure the trained .pt files exist under "
            "490/deepfake_detector/checkpoints/ or are accessible on S3."
        )
        return None
    except Exception as e:
        st.error("An error occurred during model inference.")
        st.caption(f"Technical details: {e}")
        return None


# ---------------------------------------------------------------------------
# Remote prediction — calls the FastAPI backend (490/app.py) over HTTP.
# ---------------------------------------------------------------------------

def remote_predict(tmp_path: str, modality: str, api_url: str) -> dict | None:
    """POST the file to the running FastAPI backend and return the result."""
    headers: dict[str, str] = {}
    try:
        api_key = st.secrets.get("DEEFAKE_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
    except Exception:
        pass

    endpoint = f"{api_url.rstrip('/')}/predict/{modality}"

    try:
        with open(tmp_path, "rb") as f:
            resp = requests.post(
                endpoint,
                files={"file": f},
                headers=headers,
                timeout=120,
            )
        resp.raise_for_status()
        result = resp.json()
        if not isinstance(result, dict):
            raise ValueError("API did not return a JSON object")

        prob = float(result.get("prediction_score") or result.get("probability", 0))
        label = result.get("verdict", result.get("label", "unknown")).lower()
        if label == "fake":
            label = "deepfake"
        return {"label": label, "probability": prob, "detail": result.get("detail")}

    except requests.exceptions.RequestException as e:
        st.error(
            "Could not reach the deepfake detection API. "
            "Check the API URL and make sure the backend is running.",
            icon="⚠️",
        )
        st.caption(f"Technical details: {e}")
        return None
    except (ValueError, KeyError) as e:
        st.error("The API returned an unexpected response format.", icon="⚠️")
        st.caption(f"Technical details: {e}")
        return None
    except Exception as e:
        st.error("Unexpected error during API call.", icon="⚠️")
        st.caption(f"Technical details: {e}")
        return None


# ---------------------------------------------------------------------------
# Public entry point — called by Home.py
# ---------------------------------------------------------------------------

def run_analysis(
    uploader,
    modality: str,
    use_remote: bool,
    api_url: str,
) -> dict | None:
    """Run deepfake analysis on the uploaded file.

    Args:
        uploader:   Streamlit file uploader object.
        modality:   "image", "video", or "audio".
        use_remote: True → call HTTP API; False → run model locally.
        api_url:    Base URL of the FastAPI backend (used when use_remote=True).

    Returns:
        dict with "label" and "probability", or None on error.
    """
    if not uploader:
        st.warning("Please upload a file first.", icon="⚠️")
        return None

    with st.spinner("Analyzing… this may take a moment"):
        suffix = Path(uploader.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploader.getbuffer())
            tmp_path = tmp.name

        if use_remote:
            result = remote_predict(tmp_path, modality, api_url)
        else:
            result = local_predict(tmp_path, modality)

        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    return result
