# SocialFlow AI — Social Media Post Generator

Generate AI-powered social media posts (image + caption) for Instagram, LinkedIn & Twitter.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python Flask |
| Frontend | HTML + CSS + Vanilla JS |
| Image Generation | HuggingFace Inference API (Stable Diffusion) |
| Caption Generation | HuggingFace Inference API (Mistral / Zephyr / Flan-T5) |
| Database | Firebase Firestore |
| Auth | Firebase Authentication |

>  **ONE HuggingFace API key** is used for both image AND caption generation via different models.

---

## File Structure

```
socialai/
├── app.py                  ← Flask backend (all API logic)
├── requirements.txt
├── .env.example            ← Copy to .env and fill in
└── templates/
    ├── index.html          ← Login + Signup page
    ├── dashboard.html      ← Post generator
    ├── history.html        ← Post history
    └── settings.html       ← Account settings
```

---

## ⚡ Quick Setup

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Get your HuggingFace API Key
1. Go to https://huggingface.co/settings/tokens
2. Click **New token** → select **Read** → copy it

### Step 3 — Set up Firebase
1. Go to https://console.firebase.google.com
2. Create a new project
3. Enable **Authentication** → Email/Password
4. Create **Firestore Database** (start in test mode)
5. Go to **Project Settings** → **Your Apps** → **Add Web App**
6. Copy the `firebaseConfig` object

### Step 4 — Configure environment
```bash
cp .env.example .env
```
Edit `.env`:
```
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxxx
SECRET_KEY=any_random_string_here
```

### Step 5 — Add Firebase config to HTML files
In **all 4 HTML files**, find this block and replace with your real config:
```javascript
const firebaseConfig = {
  apiKey:            "YOUR_API_KEY",
  authDomain:        "YOUR_PROJECT.firebaseapp.com",
  projectId:         "YOUR_PROJECT_ID",
  storageBucket:     "YOUR_PROJECT.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId:             "YOUR_APP_ID"
};
```

### Step 6 — Run
```bash
python app.py
```
Open: **http://localhost:5000**

---

## Firestore Security Rules

In Firebase Console → Firestore → Rules:
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /posts/{postId} {
      allow read, write: if request.auth != null &&
        (resource == null || resource.data.userId == request.auth.uid);
    }
  }
}
```

---

## HuggingFace Models Used

### Image Generation (tried in order):
| Model | Notes |
|-------|-------|
| `stabilityai/stable-diffusion-xl-base-1.0` | Best quality, may be slow |
| `stabilityai/stable-diffusion-2-1` | Good fallback |
| `runwayml/stable-diffusion-v1-5` | Fast & reliable |
| `CompVis/stable-diffusion-v1-4` | Last resort |

### Caption Generation (tried in order):
| Model | Notes |
|-------|-------|
| `mistralai/Mistral-7B-Instruct-v0.3` | Best captions |
| `HuggingFaceH4/zephyr-7b-beta` | Great fallback |
| `tiiuae/falcon-7b-instruct` | Good alternative |
| `google/flan-t5-large` | Lightweight, always available |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `503 Service Unavailable` | HuggingFace model is loading (cold start). App waits and retries automatically. |
| Image generation fails | Free tier has rate limits. Wait 30 seconds and try again. |
| Caption is empty/garbled | Try a different tone or add more description. |
| Firebase permission denied | Add the Firestore security rules shown above. |
| Login redirects to `/` | Check that Firebase config is pasted correctly in HTML files. |

---

## Pages

| Page | URL | Description |
|------|-----|-------------|
| Login/Signup | `/` | Two-card auth page matching POSTFLOW AI design |
| Dashboard | `/dashboard.html` | Generate posts with mint preview panel |
| History | `/history.html` | View & filter all past posts |
| Settings | `/settings.html` | Change name, password, sign out |
