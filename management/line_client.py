from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    PushMessageRequest,
    ReplyMessageRequest,
    TextMessage,
)

from management.config import LINE_CHANNEL_ACCESS_TOKEN, get_env

_configuration = Configuration(access_token=get_env(LINE_CHANNEL_ACCESS_TOKEN))


def reply_text(reply_token: str, text: str) -> None:
    with ApiClient(_configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=text)])
        )


def push_text(line_user_id: str, text: str) -> None:
    """For proactive morning/evening messages — LINE's Messaging API push
    (as opposed to reply) has no time window restriction but is rate-limited
    per channel plan."""
    with ApiClient(_configuration) as api_client:
        MessagingApi(api_client).push_message(
            PushMessageRequest(to=line_user_id, messages=[TextMessage(text=text)])
        )
