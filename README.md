# GRIP — Green Reporting & Innovation Platform

A complete Python/Streamlit hackathon MVP for community environmental action:
**REPORT → AI ANALYZE → DISCUSS → TRACK → INNOVATE**.

The app includes a searchable community feed, evidence uploads, Gemini analysis,
community discussion, a status history, a Green Innovation Lab, and an activity
dashboard. Every flow works without an API key using clearly labeled local
category-based guidance. No React, JavaScript build, external image host,
authentication service, or separate database server is required.

## Run locally

Use **Python 3.12**, the version used for testing. Extract the project and open a
terminal inside `grip`, where `app.py` and `requirements.txt` are located.

```bash
pip install -r requirements.txt
streamlit run app.py
```

If the commands are not on your PATH:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, normally `http://localhost:8501`.
The database and six fictional demonstration reports are created automatically.

Optional virtual environment setup:

```bash
python -m venv .venv
```

Windows PowerShell activation: `.venv\Scripts\Activate.ps1`.
macOS/Linux activation: `source .venv/bin/activate`.
Then run the install and start commands above.

## Exact GitHub structure

Upload the **contents** of the extracted `grip` folder into the root of a GitHub
repository named `grip`. Keep these exact relative paths:

| Path | Purpose |
| --- | --- |
| `app.py` | Five-page interface, forms, rendering and navigation |
| `database.py` | Schema, transactional writes, queries and portable backup |
| `ai_service.py` | Official Google GenAI SDK, strict validation and fallback |
| `prompts.py` | Pydantic contracts, categories, statuses and instructions |
| `utils.py` | Input validation, image processing and HTML escaping |
| `seed_data.py` | Six realistic, explicitly fictional environmental cases |
| `styles.py` | Responsive CSS visual system, injected from Python |
| `requirements.txt` | Tested runtime dependency versions |
| `requirements-dev.txt` | Runtime dependencies plus pytest |
| `pytest.ini` | Test configuration |
| `tests/test_core.py` | Persistence, image, AI and failure-boundary tests |
| `tests/test_app.py` | All-page and end-to-end Streamlit AppTest coverage |
| `.streamlit/config.toml` | Theme and 8 MB upload limit |
| `.streamlit/secrets.toml.example` | Safe configuration example; no key |
| `.gitignore` | Excludes keys, databases, caches and environments |
| `README.md` | Setup, deployment, architecture and demo instructions |
| `TESTING.md` | Test results and their limits |

Do **not** commit `.streamlit/secrets.toml`, `.env`, `.venv`, `data/`, any database
backup, or Python caches. GitHub's browser upload may omit dot-prefixed folders:
create `.streamlit/config.toml` and `.streamlit/secrets.toml.example` using
**Add file → Create new file** if needed. Confirm those paths appear afterward.

Alternatively, create an empty GitHub repository and run these commands inside
the extracted project. Replace YOUR_USERNAME with your GitHub username:

```bash
git init
git add .
git commit -m "Build GRIP environmental action MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/grip.git
git push -u origin main
```

## Gemini configuration

Obtain an API key from [Google AI Studio](https://aistudio.google.com/apikey).
For local development, copy `.streamlit/secrets.toml.example` to
`.streamlit/secrets.toml` and enter your key there:

```toml
GEMINI_API_KEY = "YOUR_ACTUAL_API_KEY"
GEMINI_MODEL = "gemini-2.5-flash"
GRIP_SEED_DEMO = "true"
```

`GEMINI_API_KEY` and `GEMINI_MODEL` can also be environment variables.
Environment variables take precedence over Streamlit secrets. The selected model
must support image input and structured output and be available to your key.
The model is configurable because provider availability can change.

The sidebar's **Use local demo guidance** toggle bypasses Gemini. A new session
with a configured key defaults to Gemini; without a key it defaults to local
mode. If you add a key during an existing session, turn off that toggle.
The key is never printed, included in JSON exports, or sent to the browser.

The integration uses `from google import genai`, `Client`,
`client.models.generate_content`, `types.Part.from_bytes`, JSON Schema and
Pydantic validation, following the
[official Google GenAI Python SDK](https://googleapis.github.io/python-genai/).
The deprecated `google-generativeai` package is not used.
Requests have a 25-second HTTP timeout and no automatic retry loop. Blocked,
empty, malformed, invalid, unavailable-model and failed responses all fall back
to a local template. No automatic provider call occurs just from browsing pages.
Refreshing analysis cannot replace a saved Gemini result with a failed fallback.

## Exact Streamlit Community Cloud deployment

1. Push the repository with the structure above to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
3. Select **Create app**, then **Yup, I have an app** if prompted.
4. Choose your repository, branch **main**, and main file path **app.py**.
5. Open **Advanced settings** and select **Python 3.12**.
6. For Gemini, paste the TOML block from the Gemini section into **Secrets**, replacing the key value. For offline demo mode, leave Secrets empty.
7. Save and deploy. Wait for dependency installation and app startup.
8. Open the app, confirm the feed appears, and run the demo below.

For an existing deployment, update credentials in its app settings under
Secrets. Never upload an actual secrets file to GitHub. See Streamlit's
[deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
and [secrets instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

There is no `packages.txt` or frontend build step. `requirements.txt` installs
all runtime dependencies; do not select `requirements-dev.txt` for deployment.

## Three-minute hackathon demo

1. Open **Community feed** and point out the search, filters and fictional demo labels.
2. Choose **Report an issue**, then **Use Skardu demo example**.
3. Attach your own relevant JPEG, PNG or WebP photo if available. Photos are optional; do not present unrelated images as evidence.
4. Select **Publish report & analyze**. The saved report opens automatically. Gemini or local guidance is labeled explicitly.
5. Read the possible causes and next actions in **Evidence & analysis**.
6. Open **Community discussion**, enter a display name and a useful comment, then post it.
7. Open **Progress history**, enter a name and a review note, check the acknowledgment, and select **Move to Under Review**.
8. Return to **Evidence & analysis** and select **Build a solution in Innovation Lab**.
9. Enter “Five volunteers, four weeks, local shop support” and generate a solution. Review the collection pilot, possible business model and success metrics.
10. Open **Dashboard** to see the report and pilot counts. Download a database backup before ending a hosted demo.

The remaining stages are **Verified → Action Required → Resolved**. Each stage
requires a new written basis and can advance only one step. “Verified” means
**community-reviewed**, not government, scientific, or AI verification. AI never
changes the report's status. Status history is an audit of self-declared
community actions, not proof of an incident.

## Data, images and persistence

SQLite stores reports, normalized image bytes, thumbnails, structured analysis,
comments, support signals, status history and saved innovation versions. Image
bytes are stored as BLOBs, never fragile upload paths. Every database operation
uses a short-lived connection, foreign keys and a transaction. WAL mode and a
busy timeout support modest demo concurrency. Status updates use optimistic
concurrency checks; duplicate submission tokens do not create duplicate rows.

Uploads are decoded by Pillow, checked for format and size, oriented, reduced
to at most 1600 pixels on their longest side, and re-encoded to JPEG without
EXIF metadata. A 640×360 thumbnail is stored for the feed. Images over 8 MB,
over 24 megapixels, damaged images and unsupported actual formats are rejected.
Seed cases intentionally contain no evidence photographs. Uploaded photos
appear in both the feed and report details without external image requests.

**Cloud limitation:** local SQLite data is not durable hosted storage. Files on
Streamlit Community Cloud can be removed when an app's environment is recreated.
Image BLOBs eliminate broken upload paths, but do not make local disk permanent.
See Streamlit's note on local storage in
[Connecting to data](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data).

Use **Dashboard → Download a workspace backup → Prepare database backup** to
create a consistent complete SQLite snapshot. Download it. To restore locally:
stop Streamlit, move the existing `data` directory aside, create a fresh `data`
directory, place the downloaded file there as `grip.db`, and restart. Do not
restore a database file while the app is running. Backups include all uploaded
images and public discussion; keep them private. In-app restore is deliberately
not exposed to unauthenticated visitors.

The `GRIP_DB_PATH` environment variable can select a different local database
path. `GRIP_SEED_DEMO = "false"` prevents initial seeding in a fresh database;
it does not remove existing demo rows. Feed and dashboard toggles can exclude
existing demo scenarios. There is no destructive reset control in the app.

## Scope and responsible interpretation

- All visitors share one workspace; names are self-declared. There is no authentication or permission model, as requested. Anyone with access can comment, advance statuses, generate plans and download the full workspace backup.
- Support is limited to one signal per report per Streamlit session. A new session can support again; this is not abuse-resistant voting or a count of unique people.
- Local guidance uses category-specific templates. It does not inspect images or adapt a design algorithmically to resources; entered constraints are carried forward for validation.
- Advisory priority is not a verified severity score. Local guidance always starts at Medium and states that default explicitly.
- AI text and images cannot establish the truth of a report. Causes, business opportunities and environmental benefits need local validation.
- User and AI text are HTML-escaped. Database inputs use SQL parameters. Only trusted application CSS/HTML is injected; no untrusted HTML is executed.
- With Gemini enabled, report text and evidence photos are sent to Google. The reporting form discloses this. The Innovation Lab sends report text and entered constraints.
- Dashboard numbers describe platform activity, not environmental outcomes or measured pollution reduction.
- There is no automatic duplicate detection. Search helps people find related reports before submitting; semantic deduplication is future scope.

Future scope only: durable managed storage, authentication and moderation,
stronger abuse prevention, semantic duplicate clustering, independent evidence
review, maps, institutional integrations, and measured pilot outcomes. No
payments, courses, certificates or unrelated modules are included.

## Tests and troubleshooting

From the project root:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use temporary databases and do not call Gemini or modify your app data.
See `TESTING.md` for the completed checks and limits.

| Symptom | What to do |
| --- | --- |
| Local guidance appears despite a key | Turn off the sidebar demo toggle; check model access, quota and the key in secrets. Safe fallback preserves the flow. |
| Image rejected | Use a valid JPEG, PNG or WebP below 8 MB and 24 megapixels. |
| Workspace storage error | Check disk space and write permission on the database directory, then retry. |
| Styles change after a dependency update | Use the tested dependency pins in `requirements.txt`; some CSS targets Streamlit's rendered structure. |
| Hosted data disappears | Restore a saved backup locally; Community Cloud local disk is not guaranteed durable. |
| Page appears empty after filtering | Clear the search or include demo scenarios. |
