# GRIP validation

Tested with Python 3.12 and the exact runtime dependency versions in
`requirements.txt`. Tests run from the project root against isolated temporary
databases; no actual API key is used or included.

## Automated result

```text
18 passed
```

Run again with:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

| Area | Verified behavior |
| --- | --- |
| Startup | All modules compile; Streamlit starts and its health endpoint returns HTTP 200 / `ok` |
| Pages | Feed, report form, details, Innovation Lab and dashboard run through official Streamlit AppTest without exceptions |
| Complete flow | Skardu example → submit → stored report → comment → Under Review → saved innovation plan → feed support → updated dashboard → backup |
| Upload flow | Same complete flow with a PNG uploaded through AppTest's file uploader; normalized image persists in SQLite |
| Images | Valid PNG normalization, thumbnails, metadata stripping, empty/corrupt images and oversized uploads |
| Persistence | Reports, image bytes, comments, votes, all five status events, saved innovation and backup contents |
| Duplicate writes | Repeated report/comment submission tokens create only one row |
| Concurrency | Four simultaneous seed attempts create one seed dataset; stale status changes fail without false history |
| Search & filtering | Text, category, status and demo exclusion; literal SQL-like search text does not alter the query |
| Empty/invalid states | No-results feed, zero-report dashboard and rejected report validation |
| Local mode | All six categories produce schema-valid analysis and innovation plans |
| AI request | Mocked official Google GenAI client receives JSON Schema, configured timeout, report data and correctly encoded image part |
| AI validation | Valid fenced JSON accepted; missing fields, invalid priority, blank summary and extra fields rejected |
| AI failure | Timeout/malformed response falls back with a clear notice; no key or private exception details appear in the result |
| Text safety | HTML escapes are applied to untrusted strings before custom rendering |

## Browser checks

A local Chromium/Playwright session rendered all five pages with no uncaught
browser page errors. Desktop screenshots were inspected at 1440×1100. The feed
was also inspected at 390×844; document width and scroll width were both 390px,
with stacked controls and no horizontal page overflow. The generated screenshots
are development checks rather than bundled evidence images.

## What this does not establish

- A live Gemini success response was not tested: no user's API key was supplied. SDK request construction, image payload, response validation and failures were tested with mocks. Run one real request with your own key before presenting live AI.
- No actual GitHub repository was created and no Streamlit Cloud deployment was performed. The repository is prepared for those steps, with exact instructions in `README.md`.
- Browser checks cover representative desktop and mobile sizes, not every browser or a formal accessibility audit.
- This is not a security or load certification for an unauthenticated public community service. It is a shared hackathon workspace with the limits documented in `README.md`.
- Sample reports, comments and histories are fictional demonstration content, not validated environmental incidents.
