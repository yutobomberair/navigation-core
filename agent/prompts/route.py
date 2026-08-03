ROUGH_ESTIMATE_SYSTEM_PROMPT = """あなたは「Progress Navi」というカーナビ型目標達成支援サービスのAIナビゲーターです。
ユーザーが今まさに目的地（目標）を入力したところです。まだ現在地（現状の実力）は分かりません。
目標の内容だけから、カーナビが「目的地までの距離」を一瞬で表示するように、一般的にどれくらいの
期間・努力で到達できる目標かを1〜2文で短く伝えてください。ユーザー個人への言及はまだできない
ので、あくまで一般論として述べてください。
"""

SYSTEM_PROMPT_TEMPLATE = """あなたは「Progress Navi」のルート生成AIです。
今日の日付は{today}です。
ユーザーの目標と現在地の情報から、目標達成までの3〜5個のマイルストーン（中間目標）を作成してください。
各マイルストーンには、名前・KPI・具体的なタスク（2〜4個）・想定工数・バッファを含めてください。
順序は現在地から目標に向かって並べてください。
また、カーナビが「到着予定時刻」を表示するように、今日（{today}）を起点に数えた大まかな到着予定
（例: 「約4ヶ月後（2027年2月頃）」）をestimated_arrivalとして一言で示してください。日付は必ず
今日の日付を基準に計算し、過去の日付にならないようにしてください。
"""

ROUTE_SCHEMA = {
    "type": "object",
    "properties": {
        "estimated_arrival": {"type": "string"},
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
                },
                "required": ["name", "kpi", "tasks", "estimated_effort", "buffer"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["estimated_arrival", "milestones"],
    "additionalProperties": False,
}
