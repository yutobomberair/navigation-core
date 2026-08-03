"""Self-driving smoke test for the whole user journey.

Launches the app with AI responses mocked (PROGRESS_NAVI_MOCK_AI=1, see
agent/mock.py) on a throwaway port, drives it with Playwright through
Title -> Onboarding (navigation-style wizard: destination -> current position
-> diagnostic checkpoint -> confirm) -> Navigation -> DailyCheckIn (all three
tabs), and checks each step for an uncaught Streamlit exception / expected
content.

Why mocked AI: this exercises all the real code paths that actually break
in practice (DB writes, JSON/UUID serialization, page navigation, widget
wiring) without depending on real OpenAI output or spending API credits.
It still needs a real Supabase project configured via .streamlit/secrets.toml
(SUPABASE_URL / SUPABASE_KEY) — only the OpenAI calls are stubbed. Each run
creates a fresh throwaway user (?u=e2e-<random>) so it doesn't touch or
depend on real tester data.

Requires: pip install playwright && playwright install chromium

Usage:
    python tests/e2e_smoke.py
"""

import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / "venv" / "Scripts" / "python.exe"
PORT = 8502
BASE = f"http://localhost:{PORT}"
CODE = f"e2e-{uuid.uuid4().hex[:8]}"
SCREEN_DIR = Path(__file__).resolve().parent / "screenshots"
SCREEN_DIR.mkdir(exist_ok=True)

results = []


def check(label, condition, page=None):
    status = "PASS" if condition else "FAIL"
    results.append((label, status))
    print(f"[{status}] {label}")
    if not condition and page is not None:
        shot = SCREEN_DIR / f"fail_{label.replace(' ', '_')}.png"
        page.screenshot(path=str(shot), full_page=True)
        print(f"  screenshot: {shot}")
        print("  page text snippet:", page.inner_text("body")[:500])


def has_error(page) -> bool:
    return "Traceback" in page.inner_text("body")


def run_steps(page, base, code):
    # 1. Title page via personal link
    page.goto(f"{base}/?u={code}", wait_until="networkidle")
    page.wait_for_timeout(1000)
    check("Title page loads without error", not has_error(page), page)
    check("No 個別リンク error", "個別リンクから" not in page.inner_text("body"), page)

    start_btn = page.get_by_role("button", name="旅を始める")
    check("旅を始める button visible", start_btn.count() > 0, page)
    start_btn.click()
    page.wait_for_timeout(1500)

    # 2. Onboarding wizard — step 1: destination
    check("Onboarding page loads without error", not has_error(page), page)
    dest_input = page.get_by_placeholder("例: TOEIC800点")
    check("Destination input visible", dest_input.count() > 0, page)
    dest_input.fill("TOEIC800点取りたいです")
    page.get_by_role("button", name="ルートを検索する").click()
    page.wait_for_timeout(2000)

    # step 2: current position
    check("Current position step loads without error", not has_error(page), page)
    check("Rough estimate shown", "モック応答" in page.inner_text("body"), page)
    current_input = page.get_by_placeholder("例: TOEIC500点くらい")
    check("Current position input visible", current_input.count() > 0, page)
    current_input.fill("TOEIC500点くらいです")
    page.get_by_role("button", name="距離を算出する").click()
    page.wait_for_timeout(3000)

    # step 3: checkpoint (diagnostic test, mocked 4 MC questions)
    check("Checkpoint page loads without error", not has_error(page), page)
    check("Checkpoint intro text shown", "ナビ開始前のご確認" in page.inner_text("body"), page)
    radio_groups = page.locator('[data-testid="stRadioGroup"]')
    check("Mock assessment questions rendered", radio_groups.count() == 4, page)
    for i in range(radio_groups.count()):
        radio_groups.nth(i).get_by_text("A", exact=True).click(force=True)
    page.get_by_role("button", name="確認を完了する").click()
    page.wait_for_timeout(3000)

    # step 4: confirm route and start navigation
    check("Confirm step loads without error", not has_error(page), page)
    check("Estimated arrival shown", "到着予定" in page.inner_text("body"), page)
    page.get_by_role("button", name="ナビゲーション開始").click()
    page.wait_for_timeout(1500)

    # 3. Should land on Navigation with mocked milestones
    check("Navigation reached without error", not has_error(page), page)
    body_text = page.inner_text("body")
    check("Today's Route section present", "Today's Route" in body_text, page)
    check("Map section present", "Map" in body_text, page)
    check("Mock milestone shown", "モックステップ1" in body_text, page)

    complete_btn = page.get_by_role("button", name="を完了する", exact=False)
    check("Milestone complete button visible", complete_btn.count() > 0, page)
    if complete_btn.count() > 0:
        complete_btn.first.click()
        page.wait_for_timeout(1500)
        check("No error after completing milestone", not has_error(page), page)
        body_text2 = page.inner_text("body")
        check("Current position advanced to step 2", "モックステップ2" in body_text2, page)

    # 4. DailyCheckIn — morning tab
    nav_btn = page.get_by_role("button", name="今日のナビへ")
    check("今日のナビへ button visible", nav_btn.count() > 0, page)
    nav_btn.click()
    page.wait_for_timeout(1500)
    check("DailyCheckIn (morning) loads without error", not has_error(page), page)
    check("Mock task shown", "モックタスク" in page.inner_text("body"), page)

    # evening tab
    page.get_by_role("radio", name="🌙 夜の振り返り").click(force=True)
    page.wait_for_timeout(500)
    went_well = page.get_by_label("できたことは？")
    struggled = page.get_by_label("困ったことは？")
    check("Evening form visible", went_well.count() > 0 and struggled.count() > 0, page)
    if went_well.count() > 0:
        went_well.fill("テストを完了できた")
        struggled.fill("特になし")
        page.get_by_role("button", name="振り返りを送信").click()
        page.wait_for_timeout(2000)
        check("No error after submitting reflection", not has_error(page), page)
        check("Mock reflection reply shown", "モック応答" in page.inner_text("body"), page)

    # consult tab
    page.get_by_role("radio", name="💬 相談").click(force=True)
    page.wait_for_timeout(500)
    consult_input = page.get_by_placeholder("相談してみましょう")
    check("Consult chat input visible", consult_input.count() > 0, page)
    if consult_input.count() > 0:
        consult_input.click()
        consult_input.fill("今日は疲れて何もしたくないです")
        consult_input.press("Enter")
        page.wait_for_timeout(2000)
        check("No error after consult message", not has_error(page), page)
        check("Mock consult reply shown", "モック応答" in page.inner_text("body"), page)

    # history expander on Navigation
    page.get_by_role("button", name="地図を見る").click()
    page.wait_for_timeout(1500)
    check("Back on Navigation without error", not has_error(page), page)
    page.get_by_text("過去履歴を見る").click()
    page.wait_for_timeout(500)
    check("History section shows without error", not has_error(page), page)


def main():
    env = os.environ.copy()
    env["PROGRESS_NAVI_MOCK_AI"] = "1"

    proc = subprocess.Popen(
        [
            str(PYTHON), "-m", "streamlit", "run", "app.py",
            "--server.port", str(PORT),
            "--server.headless", "true",
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        import urllib.request
        for _ in range(60):
            try:
                urllib.request.urlopen(BASE, timeout=1)
                break
            except Exception:
                time.sleep(1)
        else:
            print("Server did not start in time")
            print(proc.stdout.read())
            sys.exit(1)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            try:
                run_steps(page, BASE, CODE)
            except Exception as e:
                results.append((f"unexpected exception: {e}", "FAIL"))
                shot = SCREEN_DIR / "fail_unexpected_exception.png"
                try:
                    page.screenshot(path=str(shot), full_page=True)
                    print(f"  screenshot: {shot}")
                except Exception:
                    pass
            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()

    print("\n=== SUMMARY ===")
    n_fail = sum(1 for _, s in results if s == "FAIL")
    for label, status in results:
        print(f"{status}: {label}")
    print(f"\n{len(results) - n_fail}/{len(results)} passed")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
