# AI Cognitive Engine (Static Web App)

This repo is a single-file static web app: `index.html`.

## Run

Option 1: open `index.html` directly in your browser.

Option 2: run a local static server (recommended for some browser features):

```powershell
cd C:\Users\Lenovo\Desktop\AI
python -m http.server 8000
```

Then open `http://localhost:8000`.

## DashScope/Qwen TTS CORS proxy

Alibaba DashScope does not allow direct browser calls from this static app. For Qwen TTS, start the local proxy:

```powershell
cd C:\Users\Lenovo\Desktop\AI
.\start-dashscope-proxy.ps1
```

Then set the voice API URL in Settings to:

```text
http://127.0.0.1:8787/compatible-mode/v1
```

## Notes

- API keys are **not** shipped in this repo. Configure them in the in-app Settings panel.
- A backup file like `index.html.bak_*` is ignored by git via `.gitignore` by default.
- Chat/session histories are persisted in **IndexedDB** to avoid `localStorage` quota issues (so running via `http://localhost:...` is recommended; some browsers can restrict IndexedDB on `file:///` pages).
