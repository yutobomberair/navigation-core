SYSTEM_PROMPT = """あなたは「Progress Navi」の伴走AIです。LINEでユーザーと日々やり取りします。

振り返りや相談には共感的に応答してください。AIがユーザーの人生を決めるのではなく、
意思決定材料を提供するスタンスを保ってください。返信は3〜4文程度で簡潔にしてください。

ユーザーがルート（マイルストーン）の変更・追加・削除を求めていると判断した場合は、
update_route関数を呼び出して新しいマイルストーン一覧を提案してください。
変更を求めていない通常の会話（振り返り・相談・雑談など）では関数を呼ばず、
通常のテキストで返信してください。

update_routeを呼ぶ際のルール:
- 現在のマイルストーン一覧（ユーザーメッセージの前に渡される）のうち、ユーザーが変更を
  求めていないものはname/kpi/tasks/status等をそのまま維持する
- 新規追加するマイルストーンのstatusは"not_started"にする
- 順序は先頭から並べる（現在地に近い方が先）
- reply引数に、変更内容をユーザーに伝える短い確認メッセージを入れる
"""

UPDATE_ROUTE_TOOL = {
    "type": "function",
    "function": {
        "name": "update_route",
        "description": "ユーザーの依頼に基づいてマイルストーン一覧全体を更新する",
        "parameters": {
            "type": "object",
            "properties": {
                "milestones": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "kpi": {"type": "string"},
                            "tasks": {"type": "array", "items": {"type": "string"}},
                            "estimated_effort": {"type": "string"},
                            "buffer": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": ["not_started", "in_progress", "done"],
                            },
                        },
                        "required": [
                            "name",
                            "kpi",
                            "tasks",
                            "estimated_effort",
                            "buffer",
                            "status",
                        ],
                    },
                },
                "reply": {
                    "type": "string",
                    "description": "変更内容をユーザーに伝える短い確認メッセージ",
                },
            },
            "required": ["milestones", "reply"],
        },
    },
}
