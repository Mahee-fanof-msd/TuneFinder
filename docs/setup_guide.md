# TuneFinder — Installation and Setup Guide

## Overview

This guide explains how to set up TuneFinder on a Windows computer using Python and VS Code.

## Prerequisites

Install:

- Python.
- Git.
- Visual Studio Code.
- A working microphone.
- Internet access for external services.

External integrations require their respective API credentials.

## Step 1: Clone the Repository

Open PowerShell or the VS Code terminal.

```powershell
git clone https://github.com/Mahee-fanof-msd/TuneFinder.git
```

Navigate into the project:

```powershell
cd TuneFinder
```

> 💡 All commands in this guide must be run from the project root — the folder that contains `app`, `frontend`, and `scripts`.

## Step 2: Create a Virtual Environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, review your local execution policy before changing it.

## Step 3: Install Dependencies

```powershell
python -m pip install --upgrade pip
```

```powershell
pip install -r requirements.txt
```

For running the automated tests, also install:

```powershell
pip install -r requirements-dev.txt
```

## Step 4: Configure Environment Variables

Copy the example file to create your `.env` in the project root:

```powershell
copy .env.example .env
```

The application uses external credentials for services including:

- AudD.
- Cyanite.
- Groq.
- Tavily.

Example configuration:

```dotenv
API_URL=http://127.0.0.1:8000
AUDD_API_KEY=your_audd_key
CYANITE_API_TOKEN=your_cyanite_token
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
```

The variable names must match those used by the service modules in `app/services/`. Confirm them in the source code.

Do not upload the `.env` file to GitHub.

## Step 5: Prepare the Local Audio Catalog

Place MP3 files in `data/songs`.

The public repository does not contain commercial audio files or the development SQLite database.

Use only audio you have the rights to process.

## Step 6: Generate Fingerprints

Run:

```powershell
python -m scripts.ingest_fingerprints
```

The ingestion process creates fingerprints for the local catalog and stores them in `data/db/fingerprints.db`.

> ⚠️ The script processes **every** MP3 in `data/songs`. When adding new songs later, keep only the new files in that folder, otherwise existing songs will be fingerprinted twice.

If you already have a `fingerprints.db` file, you can copy it into `data/db/` instead of running ingestion.

## Step 7: Start FastAPI

Open a terminal with the virtual environment activated.

```powershell
python -m uvicorn app.main:app --reload
```

The backend normally runs at:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Step 8: Start Streamlit

Open a second terminal.

Activate the virtual environment if necessary.

```powershell
python -m streamlit run frontend/streamlit_app.py
```

The frontend normally opens at:

```text
http://localhost:8501
```

## Step 9: Test Recognition

1. Open the Streamlit application.
2. Play a song that has been ingested locally.
3. Record at least 10 seconds.
4. Select **Identify Song**.
5. Review the recognition result.

Recordings shorter than 10 seconds show a pop-up and reset the recorder.

If the local database cannot identify the song, the backend may attempt AudD recognition.

## Step 10: Test Recommendations

Select **Similar Songs** to submit audio for Cyanite analysis.

Check the returned recommendations and available listening links.

## Step 11: Test Music Discovery

Select **Discover by Music Preferences** and enter a natural-language preference, such as:

```text
Romantic Telugu songs from 2026
```

Review the verified results and possible matches.

## Step 12: Run Automated Tests

```powershell
python -m pytest
```

## Troubleshooting

### ModuleNotFoundError: No module named 'app'

You are running the command from the wrong folder. Change into the project root, the folder that contains `app`, and run it again.

### ModuleNotFoundError for Other Packages

Make sure the virtual environment is activated and dependencies are installed.

If a package such as `imageio-ffmpeg`, `groq`, or `tavily-python` is reported as missing, install it:

```powershell
pip install imageio-ffmpeg groq tavily-python
```

### FastAPI Does Not Start

Check whether port 8000 is already occupied, and read the traceback for missing packages.

### Streamlit Does Not Start

Confirm Streamlit is installed in the active virtual environment.

If Windows blocks `streamlit.exe` with an Application Control policy, use the `python -m streamlit run frontend/streamlit_app.py` form shown above.

### No Song Found

Possible causes include:

- Song not present in the local database.
- Poor recording quality.
- Background noise.
- Insufficient fingerprint alignment.
- AudD recognition unavailable.

### API Authentication Error

Check:

- Environment variable names.
- API key validity.
- Account access.
- API quotas.

### Similar Songs Never Finish

If the Cyanite account has reached its plan limit, analysis does not run and the webhook never reports the track as ready. Wait for the limit to reset, upgrade the plan, or configure a new API key in `.env`.

### SQLite Database Missing

Run the ingestion process after adding local songs, or copy an existing `fingerprints.db` into `data/db/`.

## Updating GitHub

After editing documentation or source code:

```powershell
git add .
git commit -m "Update TuneFinder documentation"
git push
```

Review staged files before committing to ensure no credentials, private recordings, or generated databases are included.