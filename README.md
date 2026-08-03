# navigation-core

Progress Navi — a goal-achievement navigation product (car-navigation metaphor: goal = destination, current
ability = current position, AI-generated route = the map). The Streamlit app (backed by Supabase + OpenAI) is the
original interview-testing mock and still hosts the web dashboard; a real LINE Bot (`management/`, FastAPI) is
now being built alongside it per the original product spec's LINE-first design. See `.claude/docs/PRODUCT_SPEC.md`
for the full product vision and `.claude/docs/decisions.md` for why this mock's architecture diverges from it.

## Setup

1. `venv\Scripts\Activate.ps1`
2. `pip install -r requirements.txt`
3. Run `app_platform/db/schema.sql` in the Supabase SQL editor (once, on a new project)
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in `SUPABASE_URL`, `SUPABASE_KEY`, `OPENAI_API_KEY`
5. `streamlit run app.py` (or `./run.ps1`)

## Self-testing (before asking a human to click through)

`tests/e2e_smoke.py` drives the whole app (Title → Onboarding → Navigation →
DailyCheckIn, all tabs) with Playwright against a real Supabase project but
with OpenAI calls mocked (`agent/mock.py`, gated on `PROGRESS_NAVI_MOCK_AI=1`)
— no API credits spent, no real tester data touched (each run uses a fresh
`?u=e2e-<random>` user). It launches its own server on port 8502, separate
from whatever you're running on 8501.

```
pip install -r requirements-dev.txt
playwright install chromium
python tests/e2e_smoke.py
```

Requires `.streamlit/secrets.toml` with real Supabase credentials (OpenAI key
can be a placeholder since it's never called in mock mode).

## LINE Bot (management/)

Real LINE Messaging API webhook, separate from the Streamlit app (its own `management/requirements.txt` so the
Streamlit deploy doesn't need FastAPI/uvicorn/line-bot-sdk).

1. Create a LINE Developers provider + Messaging API channel, get the Channel Secret and Channel Access Token
2. `pip install -r management/requirements.txt`
3. Copy `management/.env.example` to `management/.env` and fill in the two LINE values
4. `uvicorn management.main:app --reload --port 8000`
5. Expose it publicly for LINE's webhook (e.g. `ngrok http 8000`) and set `<ngrok-url>/webhook` as the channel's
   Webhook URL in the LINE Developers Console
6. Also run the `users.line_user_id` migration (see `.claude/docs/decisions.md`) so LINE and web identities share
   one `users` table

Current scope: every text message gets an AI reply via the same consultation persona used in DailyCheckIn — proves
out the LINE↔AI round trip. Porting the full onboarding/daily-nav/reroute flows onto LINE is still in progress.

## Deploying for user interviews

Push to GitHub and deploy via Streamlit Community Cloud, with the same three
secrets set under the app's Secrets settings.

Each tester needs their own link so their data persists across days:

```
https://<your-app>.streamlit.app/?u=<unique-code-per-tester>
```

There is no password — the `u` code in the URL is the only identity boundary,
so treat these links as unlisted/private.
