# AI Deepfake Detector — Frontend (using Streamlit)

This repository contains the **frontend web app** for our AI Deepfake Detector.
Users can upload **images**, **videos**, or **audio**, and the app will display a probability score estimating whether the media is a deepfake.

This frontend is built using **Streamlit**, and supports both:

* a **Mock API** (random results, used for demos), and
* a **Real API** (an actual deepfake detection backend)

The backend API can be swapped in by updating **Streamlit secrets**.

---

# Features

* Upload **image**, **video**, or **audio** files
* Live preview of uploaded media
* Mock mode for demos
* Real mode for production (via API)
* Clean UI with history of recent analyses
* Multipage layout (Home, About, Services, Contact)
* Auto light/dark theme styling
* Safe secrets handling for Streamlit Cloud

---

# Project Structure

```
DeepFakeFrontEnd/
│
├── Home.py                # Main page (detector UI)
├── layout.py              # UI components (settings, preview, results, etc.)
├── detectors.py           # Mock + real API calling logic
├── styles.py              # Global CSS styling
│
├── pages/                 # Extra static pages (about, contact, etc.)
│   ├── 1_About.py
│   ├── 2_Services.py
│   └── 3_Contact.py
│
└── .streamlit/
    └── secrets.toml       # API URL + API Key (ignored by Git)
```

---

# Installation (For Local Development)

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd frontend
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   # or: source venv/bin/activate (Mac/Linux)
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create your local secrets file**
   Create:

   ```
   .streamlit/secrets.toml
   ```

   Add:

   ```toml
   DEEFAKE_API_URL = "http://localhost:8000/predict"
   # Optional backend auth:
   # DEEFAKE_API_KEY = "your-secret-key"
   ```

5. **Run the app**

   ```bash
   streamlit run Home.py
   ```

---

# How the Backend API Integrates

The frontend sends uploaded files to the backend via the function:

```
real_predict()  -> detectors.py
```

When **Use mock API = OFF**, the app:

1. Reads `DEEFAKE_API_URL` from Streamlit secrets

2. Sends a POST request:

   ```
   POST /predict
   Form fields:
     file: <uploaded file>
     modality: "image" | "video" | "audio"
   ```

3. Expects the backend to return JSON like:

   ```json
   {
     "label": "deepfake",
     "probability": 0.82
   }
   ```

If anything fails (network error, 500 error, bad JSON), the app shows a user-friendly error message.

---

# Setting Secrets (LOCAL)

Make sure `.streamlit/secrets.toml` exists locally(you'll have to create it):

```toml
DEEFAKE_API_URL = "https://your-backend-url/predict"
DEEFAKE_API_KEY = "optional-token"
```

Git will **never** upload this file because it is in `.gitignore`.

---

# Setting Secrets (Streamlit Cloud)

When deploying:

1. Go to your deployed app on Streamlit Cloud
2. Click **Settings → Secrets**
3. Paste the same values:

```toml
DEEFAKE_API_URL = "https://your-production-backend.com/predict"
DEEFAKE_API_KEY = "prod-key-if-required"
```

These secrets are shared by the team on the Cloud deployment only.

---

# Multipage Navigation

Streamlit automatically creates a sidebar navigation based on the `pages/` folder.

This app shows:

* **Home** (main detector)
* **About**
* **Services**
* **Contact**

Home.py stays in the project root — do **not** move it into `/pages`.

---

# Switching Between Mock API and Real API

On the **Home** page:

1. Go to **Settings**
2. Turn **Use mock API** → OFF
3. The app now sends real API requests using the URL in secrets.toml

---

# Where to Modify Things

### To change UI layout:

* Edit `layout.py`

### To change styles:

* Edit `styles.py`

### To change backend behavior:

* Edit `real_predict()` in `detectors.py`

### To add new pages:

* Add a new `.py` file inside the `pages/` folder

---

# Important Notes

* You must create **your own** `.streamlit/secrets.toml`
* The file **does not** come from GitHub
* The backend URL and API key **must** be placed in secrets before running real mode
* All backend communication goes through `real_predict()` — no need to edit the UI

---

# Summary

This project uses Streamlit to create a clean, simple interface for detecting deepfakes from user-uploaded media. The app supports both a demo mode and real inference mode through a backend API.

You can easily maintain and extend this app due to its modular structure:

* **Home.py** -> page layout
* **layout.py** -> UI components
* **detectors.py** -> prediction logic
* **styles.py** -> styling
* **pages/** -> extra multipage content

If anyone needs to plug in a real model, they only need to update:

```
.streamlit/secrets.toml
detectors.py (if API contract changes)
```

---

