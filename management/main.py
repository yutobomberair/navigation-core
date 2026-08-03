"""LINE Bot webhook — the real counterpart to the Streamlit-simulated
DailyCheckIn page. Onboarding (destination/current position/checkpoint test)
still happens on the web wizard; everything conversational (reflection,
consultation, and now route changes) happens here instead.

Run locally with: uvicorn management.main:app --reload --port 8000
Then expose it with ngrok and set the resulting https URL + /webhook as the
LINE channel's Webhook URL (LINE Developers Console > Messaging API tab).
"""

from fastapi import FastAPI, HTTPException, Request
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from agent import reroute_agent
from app_platform.repository import checkins as checkins_repo
from app_platform.repository import goals as goals_repo
from app_platform.repository import users as users_repo
from app_platform.domain.models import ConversationMessage
from management import line_client
from management.config import LINE_CHANNEL_SECRET, WEB_APP_BASE_URL, get_env

app = FastAPI()
parser = WebhookParser(get_env(LINE_CHANNEL_SECRET))


@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = (await request.body()).decode("utf-8")

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
            _handle_text_message(event)

    return "OK"


def _handle_text_message(event: MessageEvent) -> None:
    line_user_id = event.source.user_id
    text = event.message.text.strip()

    # A message matching an existing (not-yet-linked) web user's code merges
    # that identity in, rather than starting a fresh, disconnected LINE-only
    # user — this is how "友だち追加後、コードを送ってください" on the web
    # confirm step gets reconciled back to the same account.
    by_code = users_repo.get_user_by_code(text)
    if by_code and not by_code.line_user_id:
        user = users_repo.link_line_id(by_code.id, line_user_id)
        line_client.reply_text(
            event.reply_token, "連携が完了しました！これからはLINEでやり取りしましょう。"
        )
        return

    user = users_repo.get_or_create_by_line_id(line_user_id)

    goal = goals_repo.get_latest_goal(str(user.id))
    if not goal:
        line_client.reply_text(
            event.reply_token,
            "まずはWebでルートを設定してください。\n"
            f"{WEB_APP_BASE_URL}/?u={user.code}",
        )
        return

    milestones = goals_repo.get_milestones(str(goal.id))

    checkins_repo.append_message(
        ConversationMessage(user_id=user.id, channel="checkin", role="user", message=event.message.text)
    )
    history = [
        {"role": "user" if m.role == "user" else "assistant", "content": m.message}
        for m in checkins_repo.get_conversation(str(user.id), "checkin")
    ]

    reply_text, new_milestones = reroute_agent.reply(history, goal, milestones)

    if new_milestones is not None:
        goals_repo.delete_milestones(str(goal.id))
        goals_repo.save_milestones(str(goal.id), new_milestones)

    checkins_repo.append_message(
        ConversationMessage(user_id=user.id, channel="checkin", role="ai", message=reply_text)
    )
    line_client.reply_text(event.reply_token, reply_text)
