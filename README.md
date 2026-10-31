# RetinaSight — CNN-Based Retinal Disease Screening Website

A runnable React + Flask + SQLite project scaffold for the HACK'26 Challenge 05: **CNN-Based Retinal Disease Detection from Fundus Images**. It includes an interactive dark black/blue gradient UI, a particle cursor component adapted from the provided SwarmCursor interface, image upload/preview, API validation, persistent screening records, history, CSV report download, and automated backend tests.

> **Safety / model status:** The site is runnable, but it currently uses a transparent demo placeholder. It does not classify retinal diseases and does not generate a clinical confidence score. Do not use it for diagnosis, treatment, or referral. A trained and independently validated model is required for real inference.

## Requirements

- Python 3.10–3.12 recommended
- Node.js 20+ and npm
- Windows, macOS, or Linux

## Run locally — Windows PowerShell

Open two terminals.

### 1. Backend

```powershell
cd retina-screening\backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run the backend without activating the venv:

```powershell
cd retina-screening\backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Backend runs at `http://127.0.0.1:5000`. Health check: `http://127.0.0.1:5000/api/health`.

### 2. Frontend

```powershell
cd retina-screening\frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal, normally `http://localhost:5173`.

If PowerShell reports that `npm.ps1` cannot run because script execution is disabled, use the Windows command shim:

```powershell
npm.cmd install
npm.cmd run dev
```

Optional API override: create `frontend/.env` with `VITE_API_URL=http://127.0.0.1:5000`.

## What works

- Responsive landing page and black/blue gradient styling.
- Canvas-based `SwarmCursor` component with 800 particles, swirl, pointer interaction and click burst; API is compatible with the example usage in the brief.
- Drag/drop and browse for JPG, PNG and WebP files, max 12 MB.
- Backend checks file type, decodability, image dimensions and simple brightness/contrast heuristics. These are technical checks, not clinical image-quality grading.
- SQLite database is created automatically at `backend/retina_screening.db`.
- Screening history and record detail retrieval.
- CSV report download.
- API error responses and backend tests.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | API health and model configuration status |
| POST | `/api/screenings` | Upload multipart field `image`; create record |
| GET | `/api/screenings` | List recent screening records |
| GET | `/api/screenings/<id>` | Retrieve a saved record |
| GET | `/api/screenings/<id>/report` | Download CSV summary |

## Run tests

```powershell
cd backend
python -m pytest -q
```

## Connect a trained CNN

In `backend/app.py`, replace the `demo_prediction(image)` function with an inference adapter for a model you trained and validated. The adapter should:

1. Apply exactly the same resize, color handling, normalization, and preprocessing used during training.
2. Load a trusted model artifact and a versioned class-label mapping.
3. Return calibrated class probabilities, model/version metadata, and (if validated) a severity estimate.
4. Keep `model_status` explicit; fail safely if the model file is missing or the input is out of distribution.
5. Add a Grad-CAM or similar explanation only after testing its stability and limitations.
6. Evaluate sensitivity/recall for sight-threatening classes, specificity, AUROC, calibration, subgroup performance, and external validation. Do not choose a threshold based only on overall accuracy.

Never present a raw softmax output as a medically meaningful probability without calibration and validation. Have an ophthalmology professional review the workflow before any real-world use.

## Dataset

See `dataset/README.md` and `dataset/manifest.csv`. The repository does not pretend to contain a real clinical dataset. Use properly licensed, de-identified images and preserve dataset-specific labels. See `MODEL_INTEGRATION.md` for the next steps.

## SwarmCursor note

The supplied component was adapted to a 2D Canvas implementation for straightforward Vite compatibility. It preserves the core props used by the requested example (`count`, `size`, `spread`, `swirl`, `clickEffect`) and provides animated particles, pointer interaction, and click bursts. It is not a byte-for-byte WebGL shader copy of the pasted implementation.
