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

## Notes

- API keys are **not** shipped in this repo. Configure them in the in-app Settings panel.
- A backup file like `index.html.bak_*` is ignored by git via `.gitignore` by default.
