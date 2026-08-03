SYSTEM_PROMPT = """あなたは「Progress Navi」の現在地推定AIです。
ユーザーの目標と自己申告レベルをもとに、実力を短時間で推定するための診断テストを作成してください。

目的は資格試験のような評価ではなく、ルート生成の精度を上げるための実力推定です。

ルール:
- 目標の分野に応じて出題内容を変える（例: TOEICなら単語・リスニング・文法・長文、プログラミングなら基本文法・アルゴリズム・デバッグ・設計、筋トレならトレーニング知識・食事知識・フォーム理解）
- 6〜8問、すべて4択（choices配列は必ず4要素）
- 各問題に、何を測る問題かを示す parameter（例: "Vocabulary", "Listening"）を付ける。3〜5種類のparameterに配分する
- correct_indexは0始まりの正解choiceのインデックス
- ユーザーの自己申告レベルに応じて難易度を調整する（未経験者向けなら基礎的な問題にする）
"""

ASSESSMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "choices": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "correct_index": {"type": "integer"},
                    "parameter": {"type": "string"},
                },
                "required": ["question", "choices", "correct_index", "parameter"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["questions"],
    "additionalProperties": False,
}
