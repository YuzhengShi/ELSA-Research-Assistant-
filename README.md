# ELSA Research Assistant

A local LLM-powered research assistant for managing your ELSA framework research document. Uses RAG (Retrieval-Augmented Generation) to query, add content to, and analyze gaps in your Google Doc.

## Features

- **Query**: Ask natural language questions about your 50+ page research document
- **Add Content**: Say "add", "remember", "save", "note" to append content to the right section
- **Gap Analysis**: Identify missing content and incomplete sections
- **Local & Private**: Runs entirely on your machine using Ollama
- **Google Docs Integration**: Reads from and writes to your research document
- **Chat History**: Conversations are saved and searchable

---

## Prerequisites

- Windows 10/11 with WSL2, or Linux, or macOS
- Python 3.10 or higher
- NVIDIA GPU with 12GB+ VRAM (you have RTX 5070, perfect)
- Google account
- Internet connection (for Google Docs API)

---

## Step 1: Create Project Folder

Open a terminal (PowerShell, CMD, or WSL) and run:

```bash
mkdir second-brain
cd second-brain
```

Save all the project files I provided into this folder:
- `config.py`
- `docs_client.py`
- `parser.py`
- `embeddings.py`
- `vector_store.py`
- `llm.py`
- `brain.py`
- `main.py`
- `app.py`
- `requirements.txt`

Create the static folder and save the HTML file:
```bash
mkdir static
```
Save `index.html` into the `static/` folder.

Your folder should look like:
```
├── config.py
├── docs_client.py
├── parser.py
├── embeddings.py
├── vector_store.py
├── llm.py
├── brain.py
├── main.py
├── app.py
├── requirements.txt
└── static/
    └── index.html
```

---

## Step 2: Install Python Dependencies

In the  folder, run:

```bash
pip install -r requirements.txt
```

This installs:
- `google-auth-oauthlib` - Google authentication
- `google-api-python-client` - Google Docs API
- `chromadb` - Vector database
- `ollama` - Local LLM client
- `fastapi` - Web server
- `uvicorn` - ASGI server

---

## Step 3: Install Ollama

Ollama runs LLMs locally on your machine.

### Windows

1. Go to https://ollama.com/download
2. Click "Download for Windows"
3. Run the installer
4. Follow the installation wizard
5. Ollama will start automatically and run in the system tray

### Linux / WSL

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Verify Installation

Open a new terminal and run:
```bash
ollama --version
```

You should see something like `ollama version 0.1.x`

---

## Step 4: Download LLM Models

You need two models: one for chat, one for embeddings.

### Download Qwen 2.5 14B (Chat Model)

This is ~9GB download. Run:

```bash
ollama pull qwen2.5:14b
```

Wait for it to complete (may take 10-30 minutes depending on internet speed).

### Download Nomic Embed Text (Embedding Model)

This is ~275MB. Run:

```bash
ollama pull nomic-embed-text
```

### Verify Models

```bash
ollama list
```

You should see:
```
NAME                    SIZE
qwen2.5:14b             9.0 GB
nomic-embed-text        274 MB
```

### Test the Chat Model

```bash
ollama run qwen2.5:14b "Hello, are you working?"
```

You should get a response. Press `Ctrl+D` or type `/bye` to exit.

---

## Step 5: Set Up Google Cloud Project

This allows the app to read/write your Google Docs.

### 5.1 Create a Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Sign in with your Google account
3. Click the project dropdown at the top (next to "Google Cloud")
4. Click "New Project"
5. Enter project name: `second-brain`
6. Click "Create"
7. Wait for project to be created (10-30 seconds)
8. Make sure the new project is selected in the dropdown

### 5.2 Enable Google Docs API

1. In the left sidebar, click "APIs & Services" → "Library"
2. In the search box, type "Google Docs API"
3. Click on "Google Docs API" in the results
4. Click the blue "Enable" button
5. Wait for it to enable

### 5.3 Configure OAuth Consent Screen

Before creating credentials, you need to configure the consent screen:

1. In the left sidebar, click "APIs & Services" → "OAuth consent screen"
2. Select "External" (unless you have Google Workspace, then use "Internal")
3. Click "Create"
4. Fill in the required fields:
   - App name: `Second Brain`
   - User support email: (select your email)
   - Developer contact email: (enter your email)
5. Click "Save and Continue"
6. On "Scopes" page, click "Add or Remove Scopes"
7. Search for "Google Docs API" and check the box for `.../auth/documents`
8. Click "Update"
9. Click "Save and Continue"
10. On "Test users" page, click "Add Users"
11. Enter your Gmail address
12. Click "Add"
13. Click "Save and Continue"
14. Click "Back to Dashboard"

### 5.4 Create OAuth Credentials

1. In the left sidebar, click "APIs & Services" → "Credentials"
2. Click "Create Credentials" at the top
3. Select "OAuth client ID"
4. Application type: Select "Desktop app"
5. Name: `second-brain-client`
6. Click "Create"
7. A popup appears with your credentials
8. Click "Download JSON"
9. Rename the downloaded file to `credentials.json`
10. Move `credentials.json` to your `second-brain` folder

Your folder should now have:
```
second-brain/
├── credentials.json    ← New file
├── config.py
├── ... (other files)
```

---

## Step 6: Create a Test Google Doc

Before using your real research document, test with a simple doc.

### 6.1 Create the Doc

1. Go to https://docs.google.com
2. Click "+ Blank" to create a new document
3. Name it "ELSA Test" (click "Untitled document" at top left)

### 6.2 Add Test Content

Copy and paste this into the document:

```
[INTRODUCTION]
This is a test introduction for the ELSA framework.

[D1:DEFINITION]
Domain 1 focuses on somatic and interoceptive regulation. This involves the body's ability to sense and respond to internal physiological states.

[D1:MECHANISTIC EXPLANATION]
The insula and somatosensory cortex play key roles in processing interoceptive signals.

[D1:ADAPTIVE FUNCTIONING]
Healthy interoceptive awareness allows individuals to recognize hunger, fatigue, and emotional states.

[D1:MALADAPTIVE FUNCTIONING]
Dysregulated interoception is associated with anxiety disorders and somatic symptom disorders.

[D1:CLINICAL RELEVANCE]
Clinical assessment should include measures of interoceptive accuracy and sensibility.

[D1:CLINICAL EXAMPLE: MALADAPTIVE]

[D1:CLINICAL EXAMPLE: ADAPTIVE]

[D1:CROSS-DOMAIN INTERACTIONS]

[D1:SUMMARY TABLE]

[D1:REFERENCES]

[D2:DEFINITION]
Domain 2 covers affective and emotion regulation processes.

[D2:MECHANISTIC EXPLANATION]

[D2:ADAPTIVE FUNCTIONING]

[D2:MALADAPTIVE FUNCTIONING]

[D2:CLINICAL RELEVANCE]

[D2:CLINICAL EXAMPLE: MALADAPTIVE]

[D2:CLINICAL EXAMPLE: ADAPTIVE]

[D2:CROSS-DOMAIN INTERACTIONS]

[D2:SUMMARY TABLE]

[D2:REFERENCES]

[CONCLUSION:ELSA AS INTEGRATED MECHANISTIC ARCHITECTURE]

[CONCLUSION:CLINICAL IMPLICATIONS]

[CONCLUSION:EVIDENCE GAPS AND FUTURE DIRECTIONS]

[CONCLUSION:SUMMARY]

[TABLE 7]
```

### 6.3 Get the Document ID

Look at your browser's address bar. The URL looks like:
```
https://docs.google.com/document/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit
```

The document ID is the long string between `/d/` and `/edit`:
```
1aBcDeFgHiJkLmNoPqRsTuVwXyZ
```

Copy this ID.

### 6.4 Update config.py

Open `config.py` and replace the placeholder:

```python
DOC_ID = "1aBcDeFgHiJkLmNoPqRsTuVwXyZ"  # Your actual doc ID
```

---

## Step 7: First Run

### 7.1 Start the Application

In your terminal, make sure you're in the `second-brain` folder:

```bash
cd second-brain
python app.py
```

### 7.2 Google Authentication

On first run:
1. A browser window will open automatically
2. Select your Google account
3. You may see "Google hasn't verified this app" - click "Continue"
4. Click "Allow" to grant access to Google Docs
5. You'll see "The authentication flow has completed"
6. Return to your terminal

A `token.json` file is created - this stores your authentication so you don't have to log in again.

### 7.3 Initial Indexing

The app will:
1. Fetch your document from Google Docs
2. Parse all sections
3. Generate embeddings (this takes 1-2 minutes on first run)
4. Store embeddings in ChromaDB

You'll see output like:
```
Initializing Second Brain...
Fetching document from Google Docs...
Parsing sections...
Found 25 sections
Building vector index (this may take a minute)...
Embedded: [INTRODUCTION]
Embedded: [D1:DEFINITION]
...
Added 15 sections to vector store
Indexed 15 sections
Ready!
```

### 7.4 Open the Web UI

Open your browser and go to:
```
http://127.0.0.1:8000
```

You should see the chat interface.

---

## Step 8: Test the Features

### Test Querying

Type in the chat:
```
What is Domain 1 about?
```

The system should retrieve relevant sections and answer based on your document.

### Test Adding Content

Type:
```
add this: Patients with panic disorder show heightened interoceptive sensitivity.
```

The system will:
1. Classify which section this belongs to
2. Ask for confirmation
3. Click "Yes" to confirm
4. Content is appended to that section in your Google Doc

Go check your Google Doc - the content should be there!

### Test Gap Analysis

Type:
```
/gaps
```

The system will analyze which sections are empty or incomplete.

### Test Re-indexing

After adding content, type:
```
/index
```

This refreshes the vector store with the latest document content.

---

## Step 9: Switch to Your Real Document

Once testing is successful:

1. Open your real ELSA research document
2. Make sure it has the markers (e.g., `[D1:DEFINITION]`, `[D2:MECHANISTIC EXPLANATION]`)
3. Get the document ID from the URL
4. Update `config.py`:
   ```python
   DOC_ID = "your-real-document-id"
   ```
5. Restart the app:
   ```bash
   # Press Ctrl+C to stop
   python app.py
   ```

---

## Usage Reference

### Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/index` | Re-index document (run after external edits) |
| `/stats` | Show completion statistics |
| `/gaps` | Analyze missing content |
| `/gaps D1` | Analyze gaps in specific domain |
| `/markers` | List all section markers |

### Adding Content

All of these work:
```
remember [content]
add [content]
add this: [content]
save [content]
note that [content]
don't forget [content]
make a note of [content]
```

To specify a section explicitly:
```
add [content] in [D1:DEFINITION]
```

### Querying

Just ask naturally:
```
What does the document say about emotion regulation?
Summarize Domain 3
What are the clinical examples for D1?
How does interoception relate to anxiety?
```

---

## Troubleshooting

### "credentials.json not found"

Make sure you:
1. Downloaded the OAuth JSON from Google Cloud Console
2. Renamed it to exactly `credentials.json`
3. Placed it in the `second-brain` folder

### "Ollama connection refused"

Make sure Ollama is running:
- Windows: Check system tray for Ollama icon
- Linux: Run `ollama serve` in a separate terminal

### "Model not found"

Pull the models again:
```bash
ollama pull qwen2.5:14b
ollama pull nomic-embed-text
```

### "Marker not found in document"

Your Google Doc must contain the exact marker text like `[D1:DEFINITION]`. Check:
- Spelling matches exactly
- Brackets are present
- No extra spaces

### Slow responses

First query after startup is slowest (loading model into GPU memory). Subsequent queries are faster.

### Out of VRAM

If you get CUDA out of memory errors, try a smaller model:

1. Edit `config.py`:
   ```python
   LLM_MODEL = "qwen2.5:7b"  # Instead of 14b
   ```
2. Pull the smaller model:
   ```bash
   ollama pull qwen2.5:7b
   ```

---

## File Structure

```
second-brain/
├── config.py           # Settings, markers, document ID
├── docs_client.py      # Google Docs API operations
├── parser.py           # Section extraction by markers
├── embeddings.py       # Text embedding generation
├── vector_store.py     # ChromaDB vector storage
├── llm.py              # LLM interface and prompts
├── brain.py            # Core orchestration logic
├── main.py             # Terminal interface (alternative)
├── app.py              # Web server
├── requirements.txt    # Python dependencies
├── static/
│   └── index.html      # Web UI
├── credentials.json    # Google OAuth (you add this)
├── token.json          # Auto-created after first auth
├── history.db          # Chat history (auto-created)
└── chroma_db/          # Vector database (auto-created)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser                          │
│                 http://127.0.0.1:8000                   │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP
                          ▼
┌─────────────────────────────────────────────────────────┐
│              app.py (FastAPI Web Server)                │
│              + SQLite chat history                      │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 brain.py (Orchestrator)                 │
│              query / add / gaps analysis                │
└───────┬─────────────────┼─────────────────┬─────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  ChromaDB     │ │  Qwen 2.5     │ │  Google Docs  │
│ (vectors)     │ │  (via Ollama) │ │  (via API)    │
└───────────────┘ └───────────────┘ └───────────────┘
```

---

## Quick Reference Card

```
SETUP CHECKLIST:
☐ Python 3.10+ installed
☐ Ollama installed
☐ qwen2.5:14b model pulled
☐ nomic-embed-text model pulled
☐ Google Cloud project created
☐ Google Docs API enabled
☐ OAuth consent screen configured
☐ OAuth credentials downloaded as credentials.json
☐ Test document created with markers
☐ DOC_ID updated in config.py
☐ pip install -r requirements.txt
☐ python app.py
☐ Open http://127.0.0.1:8000

DAILY USE:
1. Start: python app.py
2. Open: http://127.0.0.1:8000
3. Query, add content, check gaps
4. After external doc edits: /index
5. Stop: Ctrl+C
```
