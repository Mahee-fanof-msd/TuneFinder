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

## Step 4: Configure Environment Variables

Create a file named `.env` in the project root.

The application uses external credentials for services including:

- AudD.
- Cyanite.
- Groq.
- Tavily.

Example configuration:

```dotenv
AudD_API_KEY=your_audd_key
CYANITE_API_TOKEN=your_cyanite_token
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
```

The variable names must match those used by the installed service modules. Confirm them in the source code.

Do not upload the `.env` file to GitHub.

## Step 5: Prepare the Local Audio Catalog

Place audio files in the songs directory configured by the ingestion script.

The public repository does not contain commercial audio files or the development SQLite database.

Use only audio you have the rights to process.

## Step 6: Generate Fingerprints

Run:

```powershell
python -m scripts.ingest_fingerprints
```

The ingestion process creates fingerprints for the local catalog and stores them in SQLite.

## Step 7: Start FastAPI

Open a terminal with the virtual environment activated.

```powershell
uvicorn app.main:app --reload
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
streamlit run streamlit_app.py
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

If the local database cannot identify the song, the backend may attempt AudD recognition.

## Step 10: Test Recommendations

Use the application's similar-song feature to submit audio for Cyanite analysis.

Check the returned recommendations and available listening links.

## Step 11: Test Music Discovery

Enter a natural-language preference, such as:

```text
Romantic Telugu songs from 2026
```

Review the verified and unverified results.

## Troubleshooting

### ModuleNotFoundError

Make sure the virtual environment is activated and dependencies are installed.

### FastAPI Does Not Start

Check whether port 8000 is already occupied.

### Streamlit Does Not Start

Confirm Streamlit is installed in the active virtual environment.

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

### SQLite Database Missing

Run the ingestion process after adding local songs.

## Updating GitHub

After editing documentation or source code:

```powershell
git add .
git commit -m "Update TuneFinder documentation"
git push
```

Review staged files before committing to ensure no credentials, private recordings, or generated databases are included.