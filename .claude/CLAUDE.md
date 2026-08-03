# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

navigation-core ("Progress Navi") is a Streamlit multi-page web app. The UI text is in Japanese and uses a
car-navigation metaphor (現在地 = current position, ルート = route, 搭乗手続き-style journey framing) for a goal
achievement navigation product. Per `.claude/docs/PRODUCT_SPEC.md`, the real product has two surfaces — a LINE bot
for daily check-ins and a web dashboard for viewing the route — but this repo currently implements a **single-app
mock**: the LINE-style daily chat is simulated inside Streamlit rather than built as a real LINE Bot. This is an
intentional, user-confirmed scope decision for an interview-testing phase (see `.claude/docs/decisions.md`), not
a stopgap.

The app is backed by a real database (Supabase/Postgres) and calls the OpenAI API for all AI behavior (route
estimates, diagnostic test generation, route generation, daily task suggestions, reflections, consultation
replies) — there is no scripted/fake AI content.

## Commands

- Run the app: `streamlit run app.py` (equivalent to `./run.ps1`)
- Self-test the whole user journey before asking a human to click through: `python tests/e2e_smoke.py` (Playwright,
  real Supabase, OpenAI mocked — see "Self-testing" in README.md)
- Activate the venv (PowerShell): `venv\Scripts\Activate.ps1`
- Install deps: `pip install -r requirements.txt` (streamlit, pydantic, supabase, openai)

Before running, see "Secrets" below — the app will raise on first DB/AI call if secrets are missing. There is no
lint config or test suite yet.

## Architecture

**Routing:** Streamlit multi-page app. `app.py` is the entry point and immediately redirects via `st.switch_page`
to `pages/1_Title.py`. Pages navigate to each other explicitly with `st.switch_page("pages/N_Name.py")`.

**Page flow:**
1. `pages/1_Title.py` — title screen. Identifies the user (see Auth below), then routes to `4_Navigation.py` if
   they already have a saved Goal, otherwise to `2_Onboarding.py`.
2. `pages/2_Onboarding.py` — a navigation-style wizard (**not** a chat — an earlier chat-based hearing was replaced
   after user feedback that open-ended counseling-style conversation felt long and caused drop-off), tracked via
   `st.session_state.wizard_step`:
   - **destination**: one `st.text_input` for the goal title. On submit, `goal_service.get_rough_estimate` (calls
     `route_agent.rough_estimate`, a `chat_text` call with no current-state info yet) shows a quick "searching
     route..." style estimate — mimics a car nav instantly showing a rough distance before you've said where
     you're starting from.
   - **current_position**: one `st.text_input` for self-reported current ability. On submit,
     `goal_service.save_goal_and_current_state` persists Goal + CurrentState (title/current_ability only — no
     deadline/background/reason/ideal-state; those fields stay `None`, which is fine since they're nullable), then
     `goal_service.create_assessment` calls `agent/assessment_agent.py::generate_test` for a 6-8 question
     multiple-choice diagnostic (domain-appropriate, e.g. vocabulary/listening for a TOEIC goal).
   - **checkpoint**: the diagnostic test rendered as an `st.form`, framed as a "pre-drive check" (🚗 rental-car-style
     copy) rather than a bare quiz — user-requested framing to make a mandatory step feel less like an interruption.
     Scoring (`assessment_agent.score`) is local/deterministic — % correct per question `parameter` — not an AI
     call, so results are stable and don't cost a request. `goal_service.score_and_finalize_route` writes the score
     into `CurrentState.parameters` (free-form `dict[str, float]`, since parameter names vary by goal domain) and
     generates the route in one pass (no provisional route to replace, since the test always runs first now) via
     `route_agent.generate_route`, which also returns a one-line `estimated_arrival` string.
   - **confirm**: shows the estimated arrival and route preview, ends with a "ナビゲーション開始" button.
   There is no `conversation_history` logging for onboarding anymore (nothing conversational to log) and no
   resume-a-partial-attempt support — leaving mid-wizard restarts from `destination` on the next visit.
3. `pages/3_DailyCheckIn.py` — the LINE-simulation page. A radio toggle switches between 🌅 morning (today's
   route, generated once per day via `checkin_service.get_or_create_today_tasks`), 🌙 evening (free-text
   reflection, one per day), and 💬 consultation (open-ended chat, `channel="checkin"`).
4. `pages/4_Navigation.py` — dashboard: Today's Route, a Mentor Message (latest AI message from the checkin
   channel), a Map (milestone list with a computed "current position" = first non-done milestone — there is no
   stored `in_progress` state, it's derived), and an expandable history of past daily tasks/reflections.

**Auth:** No password. Each tester is identified by a `?u=<code>` query-string code on their personal link
(`app_platform/services/auth_service.py::require_user`); the code is the entire identity boundary. This is
deliberate for an interview-mock phase — treat tester links as unlisted/private, not as real auth.

**Data layer:** Supabase (Postgres) from day one — `st.session_state` alone can't survive a multi-day test or a
Streamlit Cloud restart. Schema lives in `app_platform/db/schema.sql` (run manually in the Supabase SQL editor;
there is no migration tooling). `app_platform/repository/*.py` are thin Supabase-backed CRUD functions per
aggregate (`users`, `goals`, `checkins`) — there is intentionally no repository *interface*/swappable-backend
abstraction, since the mock never runs without a DB; don't reintroduce that abstraction without a reason.
`app_platform/services/*.py` hold the actual use-case logic (onboarding finalization, daily task generation,
reflection/consultation flow) and are what pages call — pages should stay thin view code.

**AI layer:** `agent/client.py` wraps the OpenAI Chat Completions API with two helpers: `chat_text` (free-form
reply) and `chat_json` (structured output via `response_format=json_schema`, strict mode). `agent/route_agent.py`
(rough estimate + route/milestone generation), `agent/assessment_agent.py` (diagnostic test generation; scoring is
local, not an AI call), and `agent/checkin_agent.py` each pair a prompt (`agent/prompts/*.py`) with one of these
calls. Model defaults to `gpt-4o-mini`, overridable via the optional `OPENAI_MODEL` secret. `PROGRESS_NAVI_MOCK_AI=1`
(env var, not a secret) swaps in canned responses from `agent/mock.py` — used only by `tests/e2e_smoke.py`.

**Directory naming:** the shared domain/DB/service layer lives in `app_platform/`, *not* `platform/` — a plain
`platform/` package shadows Python's stdlib `platform` module and breaks imports inside openai/supabase/streamlit
itself. Don't rename it back.

**LINE Bot (`management/`):** a separate FastAPI app (own `management/requirements.txt` — FastAPI/uvicorn/
line-bot-sdk are not in the Streamlit app's `requirements.txt`) implementing the real LINE Messaging API webhook
from `PRODUCT_SPEC.md`, replacing the Streamlit-simulated DailyCheckIn as the primary daily-interaction surface
per user direction. `management/main.py` verifies the LINE signature and routes text messages through
`agent/checkin_agent.py`'s consultation persona — current scope is proving the LINE↔AI round trip; the
onboarding/daily-nav/reroute flows haven't been ported onto LINE yet, so DailyCheckIn is still the working
version of those. `app_platform/repository/users.py::get_or_create_by_line_id` links a LINE user to a `users` row
via the new `line_user_id` column (nullable — web-only users still key off `code`), auto-generating a `code` so a
LINE user can also open the web dashboard. Run locally with `uvicorn management.main:app --reload --port 8000` +
ngrok (see README.md); needs `management/.env` (`LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN` — gitignored,
copy from `management/.env.example`), which is separate from `.streamlit/secrets.toml` since it's a different
process that doesn't run inside the Streamlit runtime.

**Not yet implemented:** there's no push notification *scheduler* — LINE morning/evening messages would still
need something to trigger them proactively (a cron hitting a new endpoint, most likely) rather than only reacting
to inbound messages, and the Streamlit dashboard's `persons` table/repository exist in the schema but nothing
collects Person fields (age/personality/etc.) yet — out of scope for now.

## Secrets

`SUPABASE_URL`, `SUPABASE_KEY`, `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`) are required, via
`.streamlit/secrets.toml` locally (copy from `.streamlit/secrets.toml.example`, gitignored) or the Streamlit Cloud
app's Secrets settings in production. Never commit real values.

## See also

- `.claude/docs/PRODUCT_SPEC.md` — full product vision (LINE + web dashboard, multi-phase roadmap)
- `.claude/docs/decisions.md` — why this mock diverges from the spec (Supabase-from-day-one, simulated LINE,
  query-param auth, the `platform/` → `app_platform/` rename) and known limitations
