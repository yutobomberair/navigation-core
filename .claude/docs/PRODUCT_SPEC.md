# Progress Navi 仕様書（Draft）

## 1. プロダクト概要

### サービス名

Progress Navi（仮）

### コンセプト

> すべての人の挑戦を後押しする。

人は意志が弱いから挫折するのではない。
道に迷うから挫折する。

Progress Naviは、ユーザーの目標達成までの道のりをナビゲーションするサービス。

---

# 2. 基本思想

## カーナビ型目標達成支援

目標達成を「目的地までの移動」として考える。

| カーナビ | Progress Navi |
| ---- | ------------- |
| 目的地  | 達成したい目標       |
| 現在地  | 現在の能力・状況      |
| 地図   | 成長ルート         |
| 道案内  | 日々の行動提案       |
| 渋滞検知 | 計画との差分検知      |
| リルート | 計画修正          |

重要思想：

**AIがユーザーの人生を決めるのではなく、意思決定材料を提供する。**

最終判断はユーザー自身が行う。

---

# 3. システム全体構成

```
                 User

                  │

        LINE Official Account
        （日常コミュニケーション）

                  │

             AI Agent

                  │

        ┌────────────────┐
        │ User Database  │
        │                │
        │ Goal           │
        │ Current State  │
        │ KPI            │
        │ History        │
        └────────────────┘

                  │

          Web Dashboard

          （地図を見る場所）
```

---

# 4. プロダクト構成

## 4.1 LINE側

役割：

**毎日のナビゲーション・伴走**

ユーザーとの継続的な接点。

用途：

* 初回ヒアリング
* 今日の行動確認
* 進捗確認
* 悩み相談
* 振り返り
* モチベーション支援

---

## 4.2 Web Dashboard側

役割：

**目標までの地図を見る場所**

用途：

* 目標確認
* 現在地確認
* ルート確認
* KPI管理
* マイルストーン確認
* 過去履歴確認

現在Streamlitで開発中。

---

# 5. ユーザーモデル

## Person（本人）

ユーザー自身の情報。

保存項目：

* 年齢
* 性格
* 得意不得意
* 生活習慣
* 利用可能時間
* モチベーション傾向

---

## Goal（目的地）

達成したいこと。

保存項目：

* 目標
* 期限
* 背景
* 達成理由
* 理想状態

---

## Current State（現在地）

現在の状態。

保存項目：

* 現在能力
* 現状課題
* 不足要素
* 達成までの距離

---

# 6. Goal Navigation Flow

## 8ステップ

```
① Goal Setting
      ↓
② Goal具体化
      ↓
③ Current State分析
      ↓
④ Map生成
      ↓
⑤ Daily Navigation
      ↓
⑥ Regular Review
      ↓
⑦ Re-route
      ↓
⑧ Goal Arrival
```

---

# 7. Route生成

AIが目標達成までのルートを作成する。

例：

## TOEIC800点達成

```
START

現在 TOEIC500

↓

STEP1
Vocabulary

↓

STEP2
Listening

↓

STEP3
Reading

↓

GOAL

TOEIC800
```

ルート要素：

* マイルストーン
* KPI
* タスク
* 必要工数
* バッファ

---

# 8. Dashboard仕様

## Main Dashboard

表示項目：

### Today's Navigation

今日やること。

例：

```
Today's Route

□ 英単語30分
□ Listening20分
□ 模試復習
```

---

## Map表示

スタート地点からゴールまでを可視化。

```
START

  ● Current Position

        ↓

  STEP

        ↓

GOAL
```

---

## Mentor Message

AIからの一言。

例：

```
昨日より一歩前進しています。
今日は小さく進みましょう。
```

---

# 9. LINE AI Agent仕様

## 基本フロー

```
LINE Message

      ↓

LINE Messaging API

      ↓

Backend Server

      ↓

AI Agent

      ↓

LINE Reply
```

---

# 10. 初回ヒアリング

例：

```
AI:
こんにちは。
達成したい目標を教えてください。

User:
TOEIC800点取りたい。

AI:
いつまでに達成したいですか？

User:
半年後。

AI:
現在の英語力を教えてください。
```

取得情報：

* Goal
* Deadline
* Motivation
* Current State

---

# 11. Daily Navigation

## 朝

```
AI:

おはようございます。

今日のルートです。

・英単語30分
・Listening20分

まずは一歩進めましょう。
```

---

## 夜

```
AI:

今日の振り返りです。

できたことは？

困ったことは？

明日のルートを調整します。
```

---

# 12. 相談機能

例：

User:

```
今日は疲れて何もしたくない
```

AI:

```
疲れている日はルート変更しましょう。

最低ラインとして
単語5個だけ進めるルートにしますか？
```

---

# 13. LINEスタンプ構想

目的：

入力負荷低減。

文字入力なしで状態報告。

例：

| スタンプ | 意味      |
| ---- | ------- |
| 🔥   | やる気あり   |
| 😵   | 疲れた     |
| ✅    | 完了      |
| 💪   | 努力中     |
| 🚧   | 問題発生    |
| 🔄   | ルート変更相談 |

実装：

* LINEスタンプIDを状態入力として利用
* 必要に応じて画像認識を追加

---

# 14. 技術構成（MVP）

## Phase1

LINE Bot作成。

構成：

```
LINE
 ↓
Messaging API
 ↓
FastAPI
 ↓
OpenAI API
 ↓
LINE Reply
```

目標：

「LINEでAIと会話できる」

---

## Phase2

Database追加。

保存：

* User
* Conversation History
* Goal
* KPI
* Current State

候補：

* PostgreSQL
* Supabase

---

## Phase3

Web Dashboard連携。

```
LINE

 ↓

Database

 ↓

Streamlit Dashboard
```

---

# 15. 開発環境

利用PC：

* Windows 11
* Intel Core Ultra 7
* NVIDIA RTX5070
* RAM 32GB

初期構成：

* 自宅PCサーバー利用可能
* OpenAI API利用

---

# 16. MVP完成条件

最初のゴール：

> LINEで相談すると、目標達成までの行動をナビしてくれる。

必要機能：

* [ ] LINE公式アカウント
* [ ] Messaging API接続
* [ ] AIチャット
* [ ] 初回ヒアリング
* [ ] Goal保存
* [ ] 今日のTodo生成
* [ ] 振り返り

---

# 17. 開発優先順位

```
1. LINE公式アカウント完成

2. LINE ⇔ Backend接続

3. AI返信

4. 初回ヒアリング

5. Database保存

6. Dashboard連携
```

```
LINE = 毎日のナビ

Web = 地図を見る場所

AI = ナビゲーター
```
