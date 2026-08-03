# 実装ログ / 意思決定記録

対象: PRODUCT_SPEC.md を検証するための最初のモック実装。
目的: 数人のテスターに数日間使ってもらい、ユーザーインタビューを行う。git経由（Streamlit
Community Cloudを想定）で公開する。

## Mapのラベル簡略化＋ホバー拡大（2026-08-02）

「ノード内の番号とSTEPnの表記が冗長」「ホバー時にもっと大きく」というフィードバックを受けて
微調整。ラベルからは`STEPn`表記を削除（ノード自体に番号があるため）し、ホバー時にピン全体を
1.3倍に拡大するCSS（`transform: scale(1.3)`、`transform-box: fill-box`でSVG要素にも
正しく適用）を追加。`getComputedStyle`で`transform`の値がホバー前後で`none`→
`matrix(1.3, 0, 0, 1.3, 0, 0)`に変わることを直接確認した。

## LINE通知の実導線 + Mapのホバー式UI（2026-08-02）

### LINEアカウント連携と、ナビ開始時の実通知

これまで「LINEを友だち追加する」ボタンは単なる案内リンクで、追加してもWebのアカウントとは
繋がっていなかった（既知の課題として記録済み）。今回、実際に繋がるようにした。

- `management/main.py`: 受信メッセージが既存ユーザーの`code`と一致し、かつまだLINE未連携
  なら、新規ユーザーを作らずその既存ユーザーに`line_user_id`を紐付ける
- Onboarding確認画面: 「友だち追加→最初のメッセージで自分のコードを送る」という手順を明示
- `app_platform/services/line_notify.py`: Streamlit側から直接LINEにpush通知を送る軽量な
  実装。`management/`（line-bot-sdk等）には依存せず、生のhttpx呼び出しのみ（Streamlit側の
  requirements.txtを増やさないための判断）。トークン未設定やAPIエラー時は例外を出さず
  黙ってスキップする（通知失敗でナビ開始自体は止めない）
- 「ナビゲーション開始」ボタン押下時、LINE連携済みなら実際にpush通知を送る。連携確認は
  session_stateにキャッシュされた古いuserではなく、都度DBから再取得したものを使う
  （LINE連携はWeb側セッションと非同期に別プロセスで起きるため、キャッシュに頼ると
  「連携したのに反映されない」状態になる）

### Mapのホバー式UI

「文字数を減らして、ホバー/タップで詳細を見られるように」という要望を受けて、常時表示
していたSTEP名・KPIのラベルを、現在地のマイルストーンだけ常時表示・それ以外はホバー時のみ
表示に変更。実装は`.pn-card`と同じ「隠しマーカー＋CSS」路線ではなく、ラベル自体に
`.pn-pin-label { opacity: 0 }`、`.pn-pin:hover .pn-pin-label { opacity: 1 }`という
素直なCSSで対応。SVGの`<title>`要素もタップ端末向けのフォールバックとして追加（Streamlitは
`<script>`を除去するため、JSによる本格的なタップ切り替えは実現できない — 事前に伝えた
制約通り）。

検証はPlaywrightの`hover()`がSVGの`<g>`要素をうまくヒットテストできなかったため、
マウス座標を直接指定する方式に切り替え、さらに`full_page`スクリーンショットが撮影直前に
ビューポートをリサイズして`:hover`状態を消してしまう問題にも遭遇したため、最終的には
スクリーンショットではなく`getComputedStyle`と`:hover`セレクタのマッチ数を直接JSで
評価する方式で「本当に切り替わっているか」を確認した。

## 「LIFE NAVI」風ヴィンテージ地図デザインへの再スキン（2026-08-02）

ユーザー提供のモックアップ画像（羊皮紙背景・ゴールド配色・コンパスのアンティーク地図風UI）
を参考に、テーマを全面的に作り直した。事前にStreamlitの限界（破れた羊皮紙形状のカード、
コンパス型ゲージ、下部固定タブバーなどは困難）を伝え、了承を得た上で着手。

### 実装したもの

- `.streamlit/config.toml`: ゴールド×パーチメント配色（`primaryColor`等）、フォントをserifに
- `app_platform/ui.py`: 背景に薄い染みを重ねたパーチメント質感（画像を使わずCSSグラデーション
  のみで表現）、ボタンをゴールドグラデーションに、Mapのピン/線をゴールド・ブロンズ系に変更

### 技術的な発見: `st.container(border=True)`を確実にスタイリングする方法

これまでカードの見た目は`st.container(border=True)`任せで、Streamlit内部の自動生成クラス
（`st-emotion-cache-xxxxx`、ビルドごとに変わりうる）に依存しており、外部から確実に狙って
スタイリングする方法が無かった。今回、コンテナ内部に非表示のマーカー要素
（`<span class="pn-card-marker">`）を仕込み、CSSの`:has()`セレクタで
`[data-testid="stVerticalBlock"]:has(.pn-card-marker)`のように「このマーカーを子孫に持つ
コンテナ」を指定する方法を確立した。Streamlitの内部実装に依存せず安定して動作する。

ボタンは`data-testid="stBaseButton-*"`が安定したtestidとして使えることも確認済み（ただし
Streamlit標準の「Deploy」ボタンにも同じセレクタが当たり、意図せずゴールド化される。実害は
軽微なため許容）。

### 気づいた不具合: `1_Title.py`と`2_Onboarding.py`にCSSが適用されていなかった

`ui.inject_css()`の呼び出しが`3_DailyCheckIn.py`と`4_Navigation.py`にしか入っておらず、
最初のスクリーンショットでTitle画面のボタンが未装飾のままだったことで発覚。両ページに追加。

### 検証

Playwrightで全画面（Title/Onboarding各ステップ/Navigation/DailyCheckIn）のスクリーンショットを
撮って目視確認。`e2e_smoke.py`は31/31 PASS（1回だけ偶発的な失敗があったが再実行で解消、
再現しなかったためテスト側の一時的な不安定性と判断）。

### モックアップとの差分（事前合意通り）

- カードは通常の角丸矩形（羊皮紙が破れたような不規則形状ではない）
- 進捗はコンパス型の針メーターではなく、既存のMap/パーセンテージ表示のまま（今回は未着手）
- 下部固定タブバーは実装せず、Streamlit標準のサイドバーナビのまま

## Mapのパス図化＋マイルストーン挿入位置の指定（2026-08-02）

「もっとマップらしいパス図で」「マイルストーン追加が末尾固定で使い勝手が悪い」という
フィードバックを受けて対応。

- `app_platform/ui.py::render_map_path`: 縦一列のタイムライン表示（`render_timeline`、
  削除済み）から、START/GOALを結ぶジグザグのパス上にピンを配置するSVG表示に変更。
  完了=緑塗り、現在地=青塗り、未着手=グレーで色分け
- マイルストーン追加時に挿入位置（先頭 / 各STEPの後）を選べるように
  `goal_service.add_milestone`を拡張。実装は`reroute_agent`と同じ「全削除→並べ替えて
  再保存」方式を踏襲し、変更対象外のマイルストーンはstatusも含めて保持される
- 使われなくなった`goals_repo.add_milestone`（末尾追加専用の単純insert）は削除

### 検証

Playwrightでのプルダウン操作（BaseWeb Selectの検索可能セレクトボックス）が期待通り
自動操作できなかった（`type()`が既存値の途中に文字を挿入してしまい「No results」に
なる等）ため、UIの見た目はスクリーンショットで確認しつつ、挿入ロジック本体
（`goal_service.add_milestone`）は実データに対して直接呼び出して検証: 先頭挿入・
途中挿入のいずれも正しい順序になり、対象外マイルストーンの`status`（完了済みなど）も
維持されることを確認した。

## Web→LINEの導線ボタンを追加（2026-08-02）

これまでLINE→Webの導線（未設定ユーザーへの案内メッセージ）はあったが、逆方向
（Web→LINE）が無かったため、Onboarding完了画面とNavigation画面に「公式LINEを友だち追加
して通知を受け取る」ボタン（`st.link_button`）を追加した。リンク先はBotのベーシックID
（`@150picqb`）から生成した友だち追加URL。`app_platform/config.py`に
`LINE_ADD_FRIEND_URL`として定数化（秘匿情報ではないのでsecrets経由にはしていない）。

**既知の未解決事項**: このボタンで友だち追加してLINEでメッセージを送っても、現状は
`get_or_create_by_line_id`が**新しい別のuser行**を作ってしまい、Web版で使っていた
アカウント（code）とは連携されない。真の意味でWeb⇔LINEのアカウントを紐付けるには、
「友だち追加後、最初のメッセージで自分のcodeを送ってもらい、それを既存ユーザーと
マージする」といった仕組みが別途必要。今回は「Botの存在を知らせるボタン」を用意した
だけで、アカウント統合はまだ未実装。

## 簡易ログイン画面を追加（2026-08-02）

「毎回URLに`?u=`を打ち直すのが面倒」というフィードバックを受け、`?u=`が無い状態で
アクセスした場合にコード入力フォームを表示するようにした（`auth_service.require_user()`）。

実装時のバグ: フォーム内で`st.session_state["user_code"]`を`st.rerun()`前にセットして
しまい、次のレンダリングで「コードが変わっていなければユーザー検索をスキップする」という
既存の分岐条件が働かなくなり、`st.session_state["user"]`が一度も設定されないまま
参照されて`KeyError`になった。Playwrightで実際に「コード未入力でアクセス→入力→ログイン
→Title到達」まで動かして発見・修正し、再度PASSを確認した。

## LINE経由のAIによるルート変更（reroute）を追加（2026-08-02）

役割分担を「Web=ヒアリング〜診断テストまで、LINE=それ以降の会話（振り返り・相談・
マイルストーン修正）」に整理する方針を受けて実装。手動のマイルストーン編集UI
（Navigation画面のexpander）は、LINE版の動作確認ができるまで残す判断（ユーザー確認済み）。

### 仕組み

OpenAIのfunction calling（tools）を使い、AIが自分で「これはルート変更依頼かどうか」を
判断する。変更依頼と判断した場合のみ`update_route`関数を呼び出し、新しいマイルストーン
一覧（変更対象外の項目はstatusも含めてそのまま維持）を返す。それ以外の通常の会話
（振り返り・相談）はテキストで返信するだけで、DBは変更しない。

- `agent/client.py::chat_with_tools`: `chat_text`/`chat_json`に続く3つ目のOpenAI呼び出し
  ヘルパー。`tool_choice="auto"`でAIに判断を委ねる
- `agent/prompts/reroute.py` / `agent/reroute_agent.py`: プロンプトと実行ロジック
- `management/main.py`: LINEメッセージ受信時、ユーザーのactiveな目標とマイルストーンを
  取得し、`reroute_agent.reply`に渡す。関数が呼ばれていたら`goals_repo.delete_milestones`
  → `save_milestones`で丸ごと差し替え。会話ログ（`conversation_history`, channel="checkin"）
  はLINEとStreamlit DailyCheckInで共有しているため、Navigationの「Mentor Message」は
  どちらの経路から来たメッセージも同じように拾える
- 目標未設定のLINEユーザーには、Web版ヒアリングへの個人リンク（`?u=<code>`）を案内する

### 検証

Function callingの「変更依頼かどうかの判断」はモックでは意味がない（判断ロジックそのものが
AIの推論なので）ため、実際にAPIを2回だけ呼んで確認: (1)「今日は疲れて何もできなかった」→
ツール呼び出しなしで通常の共感的返信、(2)「リスニングが苦手なので単語を減らして
リスニングを増やしたい」→ `update_route`が呼ばれ、変更対象外の完了済みマイルストーンの
status（done）も正しく維持されたまま更新された。実際のLINEアプリからも動作確認予定。

## LINE↔AI疎通確認 完了（2026-08-02）

ローカル（`uvicorn management.main:app`）+ ngrokで実際のLINE公式アカウントからメッセージを
送り、`agent/checkin_agent.py`の相談ペルソナによるAI返信を実際に受信できることを確認した。
PRODUCT_SPEC.md Phase1のゴール「LINEでAIと会話できる」を達成。

セットアップで1点ハマった: LINE Official Account Managerの「応答メッセージ」機能
（Webhookとは別の、LINE Developers Consoleとも別画面にある設定）がオンのままだと、
Bot自身の返信に加えてLINE標準の「お問い合わせ受付ていません」的な自動応答も届いてしまう。
`manager.line.biz` の「応答設定」で応答メッセージをオフ（Webhookはオンのまま）にして解消。

ngrok側は、winget経由でインストールした版（3.3.1）がアカウント側の最小要求バージョン
（3.20.0）を満たさずエラーになったため、`ngrok update`で最新版に更新して解決。

---

## 本物のLINE連携に着手（2026-08-01）

ユーザーテストを経て「マイルストーン修正のようなAIとのやり取りは、Streamlitアプリではなく
LINEで行いたい」という方針転換があり、当初「モック段階では見送り」としていた本物のLINE Bot
（PRODUCT_SPEC.mdのPhase1）に着手した。

### 現状のスコープ

PRODUCT_SPEC.mdの開発優先順位（1.LINE公式アカウント 2.LINE⇔Backend接続 3.AI返信 ...）に
沿って、まず「LINEでAIと会話できる」というPhase1のゴールだけを実現した。

- `management/`: Streamlitアプリとは別プロセスのFastAPIアプリ。依存関係も
  `management/requirements.txt`に分離し、Streamlit Cloud側のデプロイには影響しない
- `management/main.py`: LINE Messaging APIのWebhookを受信し、署名検証後、テキスト
  メッセージを`agent/checkin_agent.py`の相談ペルソナにそのまま渡して返信する
- ローカル+ngrokでのプロトタイプ運用を想定（ユーザー確認済み）。本番ホスティング先は未定
- `users`テーブルに`line_user_id`列を追加し、LINEから来たユーザーもWebと同じ`users`
  テーブルで管理する（`code`は自動生成し、Web版ダッシュボードへの導線も残す）

### まだやっていないこと

- Onboarding（目標設定）・DailyCheckIn（朝/夜/相談）・マイルストーン修正をLINE上のAI対話に
  移植する作業。現状はどんなメッセージにも同じ相談ペルソナが返答するだけ
- 朝夜のプッシュ通知（能動的な配信）の仕組み。現状は受信メッセージへの返信のみで、能動配信
  には別途スケジューラが必要
- 本番ホスティング先の決定（自宅PCサーバー or クラウド）

### 実装中に見つけたこと

`line-bot-sdk`（v3）の`WebhookParser`は`linebot.v3.webhooks`ではなく`linebot.v3`直下に
ある。ドキュメントを見ずに書いた最初の実装ではimportエラーになったため、実際に
importしてエラーメッセージから正しい場所を特定した。FastAPIサーバーを実際に起動し、
署名なしリクエストが正しく400で拒否されることも確認済み（ダミー認証情報で起動テスト、
実際のLINEチャネルはユーザーが作成中）。

---

## ユーザーテストで見つかった不具合まとめ（2026-08-01）

実際に数日分の操作をしてもらったところ、以下3件の不具合が見つかり修正した。

### 1. 「ルート変更」の意味が期待と違う

`4_Navigation.py`の「ルート変更」ボタンが、目的地入力からの全ウィザードやり直しになって
いたが、ユーザーが期待していたのは「既存マイルストーンの編集・追加」だった。ボタンを
分離し、Navigation画面にマイルストーン編集用のexpander（追加・削除）を追加。ウィザード
やり直しは「目標を変更する（最初からやり直す）」という別ボタンとして明確化した。

### 2. 目標を終了しても別のactiveな目標が残っていた

「🏁 案内終了」ボタン（`Goal.status: active/finished`、`get_active_goal`は`status=active`
のみ返す）を追加したが、テストユーザーには過去のOnboardingやり直しで作られた**未終了の
activeな目標が複数残っていた**（「目標を変更する」が前の目標を終了させずに新規作成する
実装だったため）。1件終了させても、その下に隠れていた古いactiveな目標が代わりに表示され、
「終了しても終了しない」ように見えた。

修正: `goal_service.save_goal_and_current_state`で、新しい目標を作る前に既存のactiveな
目標があれば自動的に終了させるようにした（1ユーザー1activeゴールの不変条件を保証）。
あわせて`test1`の残存データも手動でクリーンアップ。

### 3. 目標を切り替えると「今日のタスク」が古い目標のまま

`daily_tasks`・`reflections`が「ユーザー単位で1日1件」（`unique(user_id, date)`）という
設計になっており、goalに紐づいていなかった。同日中に目標を切り替えると、既存の当日分の
行がそのまま返され、新しい目標のタスクが生成されなかった。

修正: 両テーブルに`goal_id`列を追加し、ユニーク制約を`(user_id, goal_id, date)`に変更
（DBのユニーク制約名がSupabase側で分からなかったため、`pg_constraint`から動的に制約名を
探して安全に置き換えるSQLを使用）。`checkin_service`・関連リポジトリ関数も`goal_id`を
必須で受け取るように変更。修正後、実際に「同じ日・同じユーザーで異なるgoal_idの行が両方
作れるか」を直接テストして制約が正しく更新されたことを確認した。

いずれも、UIやSupabaseの「Success」表示だけでは気づけず、**実データを直接クエリして
検証する**ことで発見・確認できた。

## ツール起因の不具合（実装バグではない）

このセッション中、ファイル書き込み系のツール呼び出しが`Tool permission request failed:
AbortError: Stream closed`で断続的に失敗する事象が複数回発生した。厄介なのは、エラーが
返っても**実際には書き込みが成功しているケースがあった**こと（例:
`goal_service.py`への`add_milestone`等の追加は、エラー表示にも関わらず実際にはファイルに
反映されていた）。そのため、この種のエラーに遭遇した際は、思い込みで再実装せず、
まず`Read`で実際のファイル内容を確認してから対応する方針にした。

---

## Onboardingをチャットからナビ風ウィザードに作り直し（2026-08-01）

「カウンセリングの時間が長くて離脱したくなる」というフィードバックを受け、チャット形式の
初回ヒアリング（`agent/hearing_agent.py`、自由入力→AIが次の質問を返す形式）を廃止し、
カーナビの目的地検索のような一問一答のウィザードに置き換えた。

### 新しいフロー

```
①「旅を始める」ボタン
②-1 目的地を1つ入力 → 「ルートを検索します」→ 一般的な目安をAIが即答（現在地はまだ考慮しない）
    → 現在地を1つ入力 → 目標＋現在地をDBに保存 → 診断テストを生成
②-2（演出上は1ステップとして）🚗「ナビ開始前のご確認」＝診断テスト（4択×6〜8問）に回答
    → 採点（決定的ロジック）→ CurrentState.parameters確定 → ルートを1回だけ生成
    （このタイミングでのみAIがマイルストーンと到着予定を計算する。以前のような
    「仮ルート生成→テストで補正→再生成」という二度手間はなくなった）
③ 到着予定・ルート概要を表示 →「ナビゲーション開始」→ Dashboard(Navigation)へ
```

診断テストの提示位置は「ナビ開始前」（レンタカーの利用規約確認のような演出）とユーザーが
指定。`agent/prompts/route.py`に`ROUGH_ESTIMATE_SYSTEM_PROMPT`を追加し、現在地が分かる前
の「検索中...」的な一般論コメントを返せるようにした。またルート生成本体
（`route_agent.generate_route`）は、マイルストーンに加えて`estimated_arrival`
（「約4ヶ月後」等の一言）も返すようスキーマを拡張した。

### 削除したもの

- `agent/hearing_agent.py` / `agent/prompts/hearing.py`: チャット形式のヒアリングは完全に
  不要になったため削除（目標名・自己申告レベルは`st.text_input`で直接受け取るため、AIに
  よる自由文からの項目抽出そのものが不要になった）。
- `ConversationMessage.channel`から`"onboarding"`を削除（チャットが無くなったのでログする
  対象がない）。過去のテストで作成された`channel="onboarding"`の行は履歴として残るが、
  今後書き込まれることはない。
- `goal_service.generate_provisional_route`と「仮ルート→削除→再生成」のロジック:
  テストが常にルート生成より先に行われるようになったため、仮ルートを作る意味がなくなった。

### 自己検証

`tests/e2e_smoke.py`をウィザードの4ステップ（目的地入力→現在地入力→診断テスト回答→確認）
に合わせて全面的に書き換え、Playwrightで31項目全てPASSを確認。加えて各ステップの
スクリーンショットを目視確認し、「レンタカー規約」演出（🚗アイコン付きの確認画面）が意図通り
表示されていることも確認した。

### 回帰バグ: 到着予定日がまた古い年になる（2026-08-01）

以前`hearing_agent`の期限計算で発生し、システムプロンプトに今日の日付を渡すことで修正した
のと同じ種類のバグが、`route_agent`の`estimated_arrival`計算で再発した（例:
「約2ヶ月後（2024年1月頃）」）。原因は、ウィザード化に伴い`hearing_agent`を削除した際、
そちらに入れていた日付注入のロジックを新しい到着予定日計算側に移し忘れたこと。

`agent/prompts/route.py`のSYSTEM_PROMPTをテンプレート化し、`agent/route_agent.py::generate_route`
で`date.today()`を埋め込むように修正。モックテストでは文言までは検証できないため、実際に
OpenAI APIを1回呼び出して`estimated_arrival`が正しい年（2027年2月頃）になることを確認した。

**教訓**: 日付を扱うAI呼び出しを新設・移動する際は、モックのPASS/FAILだけでなく実APIでの
出力内容も確認する。

---

## Current State推定機能の追加（2026-08-01）

ユーザーから追加仕様（`.claude/docs/PRODUCT_SPEC.md`とは別に、初回ヒアリングの質問数を
最小化し、AIが診断テストで現在地を推定するという仕様）を受けて実装。

### スコープ判断

- **適応型テスト（リアルタイム難易度調整）は実装しない**: 仕様書内でも「将来」と明記され
  ているため、今回は固定8問（実際はAIが6〜8問生成）のテストに留めた。
- **採点はAI呼び出しではなく決定的ロジック**: 4択形式にし、正解インデックスとの比較だけで
  パラメータ別スコアを計算する（`agent/assessment_agent.py::score`）。AI採点にすると
  結果が安定しない・API呼び出しが増える、というデメリットがあるため。
- **初回ヒアリングを大幅に削減**: `agent/hearing_agent.py`が収集する項目を
  goal_title・current_ability（自己申告レベル）の2つだけに削減。期限・背景・理由・
  理想状態などは聞かない（Goal/CurrentStateモデル上はnullableなので後方互換）。

### フロー

```
チャット（目標＋自己申告レベルのみ） 
      ↓ 
仮ルート生成・保存（goal_service.generate_provisional_route） 
      ↓ 
診断テスト生成（agent/assessment_agent.py::generate_test、4択×6〜8問） 
      ↓ 
ユーザーが回答（Onboardingページのst.form） 
      ↓ 
決定的採点でCurrentState.parameters更新 
      ↓ 
既存マイルストーンを削除し、パラメータを踏まえてルート再生成
```

### データモデル変更（Supabase側の手動マイグレーションが必要）

- `current_states`に`parameters jsonb`列を追加（AIが選ぶパラメータ名は目標分野によって
  変わるため固定カラムにせずJSON）
- 新規`assessments`テーブル（questions/answersをjsonbで保持、後からの見返しにも使える）

### ハマりどころ: マイグレーションの確認方法

SupabaseのSQL Editorで「Success」と表示されても、**古いSQL（別タブ/クリップボードに
残っていた前バージョンの`schema.sql`）を実行していただけ**で、意図したDDLが反映されて
いないケースがあった。「Success」という表示だけでは何が実行されたか分からないため、以後は
`client.table(...).select(...)`を実際に叩いて列/テーブルの存在を直接確認してから次に
進むようにする。

### 自己検証

`agent/mock.py`に診断テスト用のモック応答を追加し、`tests/e2e_smoke.py`にテスト回答
フェーズ（4問全てに機械的に回答して送信）を追加。マイグレーション反映後、26/26 PASSを確認。
スクリーンショットで見た目も確認済み。

## 主要な意思決定

### 1. LINE連携はモック内で疑似再現する（本物のLINE Botは作らない）

本物のLINE公式アカウント + Messaging APIは、Webhook受信用サーバーの常時稼働など、数人への
インタビュー用モックとしては投資が重い。今回は Streamlit内に「LINE風チャットUI」
（`pages/3_DailyCheckIn.py`）を実装し、朝のナビ・夜の振り返り・相談をチャット形式で再現した。
本物のLINE Bot化は、この体験の価値が確認できてから着手する。

### 2. DBはSupabaseを採用（st.session_stateではなく最初からDBに保存）

数日間の利用が前提のため、ブラウザセッションでリセットされる`st.session_state`だけでは
永続化できない。Streamlit Cloud上のローカルファイルも永続保証がないため、ホスト型Postgres
であるSupabaseを最初から採用した。

これに伴い、「Repositoryインターフェースを抽象化してsession-state実装とDB実装を切り替え
可能にする」という当初の設計案は見送った。最初からDBを使う前提なので、切り替えの必要が
なく、抽象化はYAGNIと判断。`app_platform/repository/`配下はSupabaseを直接叩く関数のみ。

### 3. ログインはURLクエリパラメータ方式（パスワード無し）

テスターごとに `https://<app>/?u=<コード>` という個別リンクを発行し、`?u=`の値をユーザー
識別子として扱う。日をまたいでも同じリンクを開けば同じデータに戻れる。本格的な認証は
実装していないため、リンクの推測・共有には注意が必要（インタビュー用途として許容）。

実装: `app_platform/services/auth_service.py` の `require_user()`。

### 4. AIは全て実際にOpenAI APIを呼び出す（固定シナリオにしない）

初回ヒアリング・ルート生成・朝のタスク提案・夜の振り返り返信・相談返信は、全て実際に
OpenAI Chat Completions APIを呼び出す。固定文言にすると「AIが自分に合わせて考えてくれる
か」という一番検証したい価値が測れなくなるため。構造化データの抽出（ヒアリング結果、
マイルストーン、朝タスク）は`response_format=json_schema`で行っている。

### 5. ディレクトリ名 `platform/` → `app_platform/` にリネーム

実装中に判明: `platform/`はPythonの標準ライブラリ`platform`モジュールと名前が衝突し、
openai/supabase/streamlitなど内部で`import platform`を使うライブラリが軒並み壊れる
（`AttributeError: module 'platform' has no attribute 'system'`）。ユーザー確認の上、
`app_platform/`にリネームした。

### 6. ページ構成の再編

既存の4ページスタブは製品の核となる体験（LINEでのチャット的やり取り）を全く表現していな
かったため、インタビューで検証する価値がある形に再構成した。

| 旧 | 新 | 変更内容 |
|---|---|---|
| `1_Title.py` | `1_Title.py` | `first_visit`というsession_stateフラグ判定を廃止し、DB上にGoalが存在するかどうかで初回/再訪を判定するよう変更 |
| `2_RouteSearch.py`（text_input1つ、保存なし） | `2_Onboarding.py` | チャット形式の初回ヒアリングに置き換え。AIとの対話でGoal/期限/背景/理由/理想状態/現状を収集し、完了したらルート（マイルストーン）をAI生成してSupabaseに保存 |
| `3_Test.py`（「分析しています」の固定文言） | `3_DailyCheckIn.py` | LINE風チャットページとして新設。「🌅朝のナビ」「🌙夜の振り返り」「💬相談」をラジオボタンで切り替え |
| `4_Navigation.py`（固定文言のみ） | `4_Navigation.py` | Today's Route・Map（マイルストーン一覧＋現在地表示）・KPI・Mentor Message・過去履歴を実装したダッシュボードに |

### 7. Personデータ（年齢・性格など）はテーブルのみ用意し、ヒアリングには未接続

`persons`テーブルとrepository関数は用意したが、初回ヒアリングのAI対話フロー
（`agent/hearing_agent.py`）ではGoal/CurrentStateに関する項目のみを収集している。今回の
モックで検証したいのは「チャットでのヒアリング→AIによるルート生成→日々のナビ→地図で
振り返る」という体験の核であり、詳細なパーソナルプロファイリングはスコープ外とした。

---

## 実装した構成

```
navigation-core/
├── app.py
├── pages/
│   ├── 1_Title.py
│   ├── 2_Onboarding.py
│   ├── 3_DailyCheckIn.py
│   └── 4_Navigation.py
├── app_platform/
│   ├── domain/models.py        # User, Person, Goal, CurrentState, Milestone,
│   │                            # DailyTask, ConversationMessage, Reflection (pydantic)
│   ├── db/
│   │   ├── client.py            # Supabaseクライアント（st.cache_resource）
│   │   └── schema.sql           # テーブル定義（Supabase側で事前実行が必要）
│   ├── repository/
│   │   ├── users.py
│   │   ├── goals.py
│   │   └── checkins.py          # daily_tasks / reflections / conversation_history
│   ├── services/
│   │   ├── auth_service.py      # require_user() 等
│   │   ├── goal_service.py      # オンボーディング確定、マイルストーン取得/完了
│   │   └── checkin_service.py   # 朝タスク生成、振り返り、相談
│   └── config.py                # st.secrets読み込み
├── agent/
│   ├── client.py                 # OpenAI APIラッパー（chat_text / chat_json）
│   ├── prompts/
│   │   ├── hearing.py
│   │   ├── route.py
│   │   └── checkin.py
│   ├── hearing_agent.py
│   ├── route_agent.py
│   └── checkin_agent.py
├── requirements.txt              # streamlit, pydantic, supabase, openai
└── .streamlit/secrets.toml.example
```

`management/`（将来の本物のLINE Bot用FastAPI）は今回未着手のまま。

---

## セットアップ手順（README.mdにも記載）

1. `app_platform/db/schema.sql` をSupabaseのSQL Editorで実行してテーブルを作成
2. `.streamlit/secrets.toml.example` を `.streamlit/secrets.toml` にコピーし、
   `SUPABASE_URL` / `SUPABASE_KEY` / `OPENAI_API_KEY` を設定（このファイルは`.gitignore`
   済みでリポジトリには含まれない）
3. `pip install -r requirements.txt`
4. `streamlit run app.py`
5. GitHubにpush → Streamlit Community Cloudでデプロイ、同じ3つのSecretsをCloud側にも設定
6. テスターごとに `https://<app>.streamlit.app/?u=<コード>` の個別リンクを発行して配布

---

## 動作確認で見つかった不具合と修正

### `st.switch_page`が`?u=`クエリパラメータを消してしまう問題（2026-08-01）

実際にローカルで動かして`?u=test1`付きURLにアクセスしたところ、常に「個別リンクから
アクセスしてください」のエラーが出て先に進めない不具合が発生。`streamlit.testing.v1.AppTest`
で再現したところ、`st.switch_page()`は呼び出されるたびに（`app.py`の自動リダイレクトだけで
なく、ボタン操作によるページ遷移も含めて）`st.query_params`をクリアすることを確認した。

これはアプリ内のほぼ全てのページ遷移がこの問題の影響を受けることを意味し、`?u=`のURLだけで
ユーザーを識別する設計の前提が崩れていた。

**1回目の修正（不十分だった）**: `auth_service.require_user()`側だけを、クエリパラメータが
消えていても`session_state`に覚えておいたコードにフォールバックする実装に変更した。しかし
`app.py`はそれまで一度も`require_user()`を呼ばずにいきなり`switch_page`していたため、
`session_state`に何もキャッシュされていない状態でクエリパラメータだけが消え、根本原因は
直っていなかった（`AppTest`での検証も、実際のバグ再現手順とズレたパターンで確認してしまい
見逃した）。

**2回目の修正（実機で確認済み）**: `app.py`で`switch_page`を呼ぶ**前**に
`auth_service.require_user()`を呼び、ブラウザの実URLがまだ生きている最初のスクリプト実行時
に`?u=`の値を`session_state`へ確定させるようにした。以降のページはこの`session_state`を
フォールバック先として使えるため、`switch_page`が`query_params`を消しても識別を維持できる。

**確認方法**: `AppTest`で「`require_user()`→`switch_page`」という実際の`app.py`と同じ
呼び出し順序を再現し、修正後は遷移先ページでも`u=test1`が正しく解決されることを確認した。

## 自己検証の仕組み（2026-08-01）

ここまでの不具合（UUID未変換、日付未渡し、プロセス多重起動など）が、ユーザーに実際に
クリックしてもらって初めて見つかる状態が続いたため、「ブラウザを自分で操作して確認する
仕組み」を導入した。

- `agent/mock.py` + `agent/client.py`の`PROGRESS_NAVI_MOCK_AI=1`判定: OpenAI呼び出しを
  固定のダミー応答に差し替えられるようにした。実際のAPIコストをかけずに、JSON抽出・DB
  保存まわりのロジック（今回バグが多発した箇所）を繰り返しテストできる。
- `tests/e2e_smoke.py`: Playwrightで実ブラウザ（Chromium）を操作し、Title→Onboarding→
  ルート生成→Navigation（マイルストーン完了操作含む）→DailyCheckIn（朝/夜/相談の全タブ）
  までを自動で一巡し、Streamlitの例外（Traceback表示）が出ていないか、期待する文言が
  表示されているかをチェックする。8502番ポートに専用サーバーを一時起動し、テスターの
  データとは無関係な使い捨てユーザー（`?u=e2e-<random>`）を使う。
- 実際にこの仕組みで動かしたところ、初回はテストスクリプト側のセレクタ指定ミス（2件、
  アプリのバグではない）を検出・修正し、最終的に23項目全てPASSを確認した。

今後の運用: コード変更後、ユーザーに動作確認を頼む前にまず`python tests/e2e_smoke.py`を
実行し、Traceback落ちのような機械的に検出できる不具合を先に潰してから依頼する。

## UIデザインの改善（2026-08-01）

初期実装のUIが素朴すぎるとのフィードバックを受け、「カード風UI＋ルート可視化の強化」の
範囲でデザインを改善した。

- `.streamlit/config.toml`: テーマカラー（primaryColor等）を設定
- `app_platform/ui.py`: 共通UIパーツを追加
  - `card()`: 枠付きカードのコンテキストマネージャ
  - `mentor_message()`: Mentor Message用の左ボーダー付き吹き出し風表示
  - `render_timeline()`: Mapを、接続線と現在地ドット付きの縦タイムライン表示に変更
    （従来の絵文字＋テキストの羅列から変更）
- 実装時のハマりどころ: 当初`card_start()`/`card_end()`という、開始タグと終了タグを別々の
  `st.markdown`呼び出しに分ける実装にしたが、**Streamlitは`st.markdown`呼び出しごとに
  独立したHTML断片としてレンダリングするため、開始タグと終了タグが実際には繋がらず**、
  中身が枠の外に表示される不具合になった。スクリーンショットで実際に確認して発見し、
  ネイティブの`st.container(border=True)`を使う方式に修正した（チェックボックスのような
  インタラクティブなウィジェットも正しく内包できる）。
- Playwrightで生成したスクリーンショットを自分で目視確認してから完了とした（`e2e_smoke.py`
  のテキストベースの検証だけでは、この「見た目だけ壊れている」不具合は検出できない）。

## 既知の制限事項

- **オンボーディング再開不可**: ヒアリング途中でページを離脱した場合、送受信メッセージは
  `conversation_history`（channel="onboarding"）に保存され後から参照はできるが、UIとしては
  次回訪問時にゼロから会話が始まる（DBの履歴を読み込んで会話を再開する処理は未実装）。
- **マイルストーンステータスは実質2値**: `Milestone.status`は`not_started/in_progress/done`
  の3値を型として持つが、実装では`in_progress`は使用せず、「先頭の未完了マイルストーン」を
  現在地として都度計算する方式にしている。
- **能動的なプッシュ通知は無し**: 本物のLINEと異なり、朝夜のメッセージはテスターが
  `3_DailyCheckIn.py`を自分から開かない限り生成されない。
- **認証はURLコードのみ**: なりすまし防止機能は無い。個別リンクの取り扱いに注意が必要。
- **Supabase接続は実機で確認済み（2026-08-01）**: `?u=`ログイン→Supabaseでのユーザー作成/
  取得までは実際にローカルで動作確認済み。ただしSupabase側で以下2点のハマりどころがあった。
  - `SUPABASE_URL`はプロジェクトのベースURL（`https://xxxxx.supabase.co`）のみを指定する。
    末尾に`/rest/v1/`を付けて設定してしまうと接続できない。
  - SQL Editorで`schema.sql`のCREATE TABLEを実行しただけでは`anon`ロールにテーブルへの
    アクセス権限が付与されず、`permission denied for table ...`になる。`schema.sql`の末尾に
    RLS無効化＋`grant`文を追加済み（新規プロジェクトでは`schema.sql`をそのまま実行すれば
    発生しない）。
  - `save_milestones`で`goal_id`（UUID型）を文字列化せずdictにマージしていたため、
    Supabaseへの保存時に`TypeError: Object of type UUID is not JSON serializable`が発生。
    `app_platform/repository/goals.py`で`str(goal_id)`に修正。他のrepository関数は全て
    pydanticの`model_dump(mode="json")`経由でシリアライズしており、同種のバグは無いことを
    確認済み。
- **エンドツーエンド動作確認 完了（2026-08-01）**: Title→Onboarding（AIとのチャットヒアリング）
  →ルート生成→Navigation（Map/Today's Route/Mentor Message）→DailyCheckInの🌅朝/🌙夜/💬相談
  の全タブまで、実際にローカルで一通り動作することを確認した。
