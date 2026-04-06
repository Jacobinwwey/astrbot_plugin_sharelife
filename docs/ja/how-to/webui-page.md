# スタンドアロン WebUI

## 用途

`sharelife` の WebUI は、AstrBot Dashboard に埋め込まなくても直接開ける独立ページです。テンプレート投稿、テンプレートパッケージのアップロード、リスクラベル確認、管理者レビュー、再試行キュー確認に使えます。
主要パネルとして、トライアル状態（Trial Status）と管理者適用ワークフロー（Admin Apply Workflow）を提供します。

## 設定

```json
{
  "webui": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 8106,
    "cors": {
      "allow_origins": ""
    },
    "security_headers": {
      "enabled": true,
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
      "Referrer-Policy": "no-referrer",
      "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
      "Content-Security-Policy": "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; form-action 'self'"
    },
    "auth": {
      "member_password": "",
      "token_ttl_seconds": 7200,
      "allow_query_token": false,
      "allow_anonymous_member": false,
      "anonymous_member_user_id": "webui-user",
      "anonymous_member_allowlist": [
        "POST /api/trial",
        "GET /api/trial/status",
        "POST /api/templates/install",
        "GET /api/member/installations",
        "POST /api/member/installations/refresh",
        "GET /api/preferences",
        "POST /api/preferences/mode",
        "POST /api/preferences/observe"
      ],
      "login_rate_limit_window_seconds": 60,
      "login_rate_limit_max_attempts": 10,
      "api_rate_limit_window_seconds": 60,
      "api_rate_limit_max_requests": 600
    },
    "observability": {
      "metrics_max_paths": 128,
      "metrics_overflow_path_label": "/__other__"
    }
  }
}
```

ポイント:

1. 認証フィールドが空なら、公開 / member 向けサーフェスを使えます。
2. 有効な WebUI パスワードを設定すると `/api/*` はログイン必須になります。
3. 管理 API の権限はログインした token のロールで判定され、リクエスト本文の `role` は信用しません。
4. 旧 `auth.password` も後方互換で使えますが、member 専用互換です。
5. 既定では query token を無効化（`allow_query_token=false`）。`Authorization: Bearer <token>` を利用してください。
6. ログイン失敗は `login_rate_limit_*` によって制限されます。
7. token の有効期限は `token_ttl_seconds` で制御します。
8. API リクエストは `api_rate_limit_*`（`client + role + path` 単位）で制限されます。
9. メトリクス path 基数は `observability.metrics_max_paths` で制御し、超過分は `metrics_overflow_path_label` に集約します。
10. `GET /api/ui/capabilities` はログイン前でも参照でき、現在の有効ロールと実行可能オペレーションを返します（UI の capability ゲート用）。
11. WebUI レスポンスには既定でセキュリティヘッダー（`X-Content-Type-Options`、`X-Frame-Options`、`Referrer-Policy`、`Permissions-Policy`、`Content-Security-Policy`）が付与され、`webui.security_headers` で調整できます。
12. Reviewer / Admin 認証手順と秘密バックアップ手順は公開ドキュメントから除外しています。
13. `allow_anonymous_member=true` を有効にすると、特定の member エンドポイント（trial/install/preferences/installations）は未ログインでも利用できますが、`anonymous_member_user_id` に固定され、他の `user_id` への越境アクセスはできません。
14. `anonymous_member_allowlist` で匿名アクセス可能な API を `"METHOD /api/path"` 形式で明示的に上書きできます。未設定時は上記の安全な既定集合を使用します。

## できること

1. 実行モードと詳細観測フラグの変更
2. Trial Status パネルで現在の `template_id` に対するトライアル状態、TTL、残り秒数を確認可能
3. テンプレート投稿とテンプレートパッケージのアップロード
4. Admin Apply Workflow パネルで dry-run、apply、rollback を同じ場所から実行可能
5. `risk_level`、レビューラベル、warning flags、prompt injection 検出結果の確認
6. 右上の Developer Mode トグルを ON にすると、リスク検出結果を `file/path/line/column` 単位で確認可能
7. Developer Mode が OFF の場合は、通常運用向けに判定レベルの情報だけを表示
8. 承認済みテンプレートのパッケージ生成とダウンロード
9. 管理者による投稿レビュー、review note と手動ラベル保存、未承認投稿パッケージのダウンロード、公開済み版との比較、再試行キュー操作、監査ログ確認
10. Templates / Submissions の表表示と、`template_id`・`category`・`tag`・`source_channel`・`risk_level`・`status`・`review_label`・`warning_flag` フィルタ
11. 公式 catalog metadata として `category`・`tags`・`maintainer`・`source_channel` をテンプレート一覧と詳細で確認可能
12. aggregate な `engagement` 指標として `trial_requests`・`installs`・`prompt_generations`・`package_generations`・`community_submissions`・`last_activity_at` をテンプレート一覧と詳細で確認可能
13. Templates ツールバーで `template_id`・`recent_activity`・`trial_requests`・`installs` による並び替えが可能
14. Submission Compare パネルで、version・risk level・review note・label 差分・prompt preview・package metadata・scan 変化を構造化カードとハイライト表示で確認可能。raw JSON も残ります
15. Template Detail / Submission Detail パネルで prompt preview、prompt length、package filename、timestamp、moderation metadata、公式 catalog metadata、aggregate engagement を確認可能
16. engagement はテンプレート単位の集計のみで、ユーザー単位やセッション単位の履歴は公開しません
17. Risk Glossary パネルで risk level・review label・warning flag の意味を確認可能
18. Profile Pack Market セクションで `artifact_id` 投稿、管理者審査、catalog フィルタ/詳細表示、risk・label・flag バッジのワンクリック絞り込み反映が可能で、runtime 比較の可視化カードはメイン画面セクションと独立 `/market` の両方で利用できます。さらに `/api/profile-pack/catalog/insights` で metrics/featured/trending のサーバー集計を取得できます
19. Profile Pack のインストールガードとして、`Plugin Install Plan` -> `Confirm Plugin Install` -> `Execute Plugin Install` を提供します。実行は既定で無効で、`profile_pack.plugin_install.enabled=true` 設定とコマンド接頭辞 allowlist + timeout の制約下でのみ有効です。
20. 審査証跡の連動表示として、compare/evidence カードに plugin install 実行状態と失敗分類（`policy_blocked` / `command_failed` / `timed_out`）を表示します。
21. `UI Locale` は `en-US` / `zh-CN` / `ja-JP` をサポートし、collection state、workspace route/summary、moderation 文言、profile-pack の空状態、detail パネルの項目ラベルまで反映されます。選択はブラウザの `localStorage` に保存され、無効な値は `en-US` にフォールバックします。
22. 独立 market ページとして `/market` を開くと、profile-pack catalog の一覧・詳細・section 指定の runtime 比較を集中して実行でき、比較結果は可視化カード・差分セクション表・警告ハイライトで確認できます。
23. `UI Locale` とボタン文言は `/`・`/member`・`/admin`・`/market` 間で同期され、ブラウザの `sharelife.uiLocale` を共有して反映されます。
24. `/member` と `/admin` は情報設計レベルで分離された専用テンプレート（member-first / admin-first）に切り替わっています。
25. ロールページのログイン役割選択はページに固定されます（`/member` は `member` のみ、`/admin` は `admin` のみ）。
26. 上部ユーティリティバーに locale クイックスイッチとコンソール導線を固定し、言語/画面切り替えを高速化しています。
27. 低頻度の操作（`Workspace route actions`、`Plugin install execution controls`、`リスク用語集`）は既定で折りたたみ表示です。
28. API 応答には追跡用の `X-Request-ID` が付与され、`/api/metrics` で Prometheus 形式メトリクス（`sharelife_webui_http_*`、`sharelife_webui_auth_events_total`、`sharelife_webui_rate_limit_total`）を取得できます。
29. Reviewer / Admin 運用、可観測性当番、認証秘密バックアップは非公開運用ドキュメントで管理し、公開サイトには載せません。
30. 認証/レート制限/内部エラーは `{"ok": false, "error": {"code": "...", "message": "..."}}` の統一フォーマットで返却されます。
31. ボタン単位の操作は `/api/ui/capabilities` によるバックエンドポリシーでゲートされ、public/member/admin の画面と token ロールを一致させます。
32. Profile-pack パネルに専用の互換性ガイダンス（issue 一覧 + クリック可能 action shortcut）を追加。対応済み issue/action はターゲット操作へジャンプし、ヒントがある場合は `plugin_ids` / 推奨 section も自動補完します。Developer Mode 専用ターゲットは有効化後に自動再開し、生の `compatibility_issues` / `action_codes` は Developer Mode のみ表示します。
33. `/market` は左ファセット + 上部検索/並び替えの情報設計（Hugging Face スタイル）に更新され、モバイルではフィルタをドロワー表示で利用できます。
34. マーケットのローカル表示状態は URL 同期（`q`、`sort`、`facet_*`、`pack_id`）に対応し、絞り込み結果と選択状態をリンク共有で再現できます。
35. デスクトップ `/market` では `Detail & Compare` を右カラムに固定表示し、`Operation Log` は profile-pack カード内トグルで既定折りたたみ表示に変更しています。
36. 管理者向けに `Storage Backup and Restore` パネルを追加し、local summary、policy 読み書き、backup job 実行/一覧/詳細、restore prepare/commit/cancel、restore job 観測まで一画面で実行できます。
37. Storage 出力は通常モードで要約表示を優先し、Developer Mode のときのみ raw JSON を追記表示します。

## 起動とアクセス

1. プラグイン初期化時に WebUI を自動起動します。
2. チャットで `/sharelife_webui` を実行して URL を確認します。
3. 目的に応じて分離されたページへアクセスします。
  - `/` フルコンソール（統合デバッグ）
  - `/member` メンバー操作コンソール
  - `/admin` 管理者操作コンソール
  - `/market` 独立マーケットページ

### コンテナ起動（クイック）

```bash
docker compose up -d --build
```

起動後は `http://127.0.0.1:8106` にアクセスしてください。  
データは `./output/docker-data` に永続化されます。
compose 既定では `state_store.backend=sqlite` を使用し、SQLite は `./output/docker-data/sharelife_state.sqlite3` に保存されます。

## トラブルシューティング

1. `permission_denied`: 現在の token が `admin` ではありません。管理者パスワードで再ログインしてください。
2. `401`: WebUI 認証が有効です。`member` か `admin` を選んで先にログインしてください。
3. `prompt_injection_detected`: アップロードしたパッケージが prompt injection ヒューリスティックに一致しました。現段階では削除ではなく高リスク表示です。
4. 手動で保存値を変更して locale 表示が崩れた場合は、`localStorage` の `sharelife.uiLocale` を削除して再読み込みしてください。
5. Developer Mode の状態が崩れた場合は、`localStorage` の `sharelife.developerMode` を削除して再読み込みしてください。
