# スタンドアロン WebUI

## 対象

Sharelife WebUI は AstrBot Dashboard に埋め込まなくても独立して動作します。
このページでは、公開 / member 側で実際に使えるフローだけを扱います。

1. Spotlight 形式のマーケット検索
2. ローカルインストール管理
3. template アップロードと profile-pack 投稿
4. member 側のタスク / 結果追跡

特権 moderation と operator フローは非公開 docs にのみ記載します。

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

## 認証の挙動

1. 認証フィールドが空なら、公開 / member サーフェスはそのまま利用できます。
2. `member_password` を設定すると、保護された member 操作にログインが必要になります。
3. `GET /api/ui/capabilities` はログイン前でも読めるため、UI はこれを基準に保護操作を制御します。
4. query token は既定で無効です。`Authorization: Bearer <token>` を使ってください。
5. ログイン試行は `login_rate_limit_*` で制限されます。
6. API リクエストは `api_rate_limit_*`（`client + role + path` 単位）で制御されます。
7. 既定レスポンスには `security_headers` が付き、`Content-Security-Policy` も含まれます。
8. `allow_anonymous_member=true` を使う場合でも、匿名で使えるのは allowlist に載った API だけで、要求は `anonymous_member_user_id` に固定されます。
9. 特権認証、secret 材料、backup/restore runbook は非公開 docs に残します。
10. standalone での「ローカル AstrBot 設定取り込み」は既定で無効です（安全優先）。必要時のみ明示的に有効化してください。
   - CLI: `python3 scripts/run_sharelife_webui_standalone.py --enable-local-astrbot-import`
   - 環境変数: `SHARELIFE_ENABLE_LOCAL_ASTRBOT_IMPORT=1`
   - 匿名主体によるローカル取り込みを許可する場合: `--allow-anonymous-local-astrbot-import` / `SHARELIFE_ALLOW_ANONYMOUS_LOCAL_ASTRBOT_IMPORT=1`

## 起動とルート

1. プラグイン起動時に WebUI の起動を試みます。
2. `/sharelife_webui` を実行して URL を確認します。
3. 公開 / member 向けルート:
   - `/` 統合エントリ
   - `/member` member コンソール
   - `/market` 独立マーケットページ
4. 制限付き operator ルートは存在しますが、公開 docs では説明しません。

### コンテナ quick start

```bash
docker compose up -d --build
```

その後 `http://127.0.0.1:8106` を開きます。
データは `./output/docker-data` に永続化されます。
Compose は既定で `state_store.backend=sqlite` を使用し、DB は `./output/docker-data/sharelife_state.sqlite3` に保存されます。

## Member ワークフロー

### 1. マーケット検索 + トライアル状態

1. `/member` と `/market` はどちらも Spotlight 形式の検索から始まります。
2. 検索結果はカタログカード、詳細、比較パネルに反映されます。
3. `トライアル状態（Trial Status）` は `not_started|active|expired` と `ttl_seconds` / `remaining_seconds` を表示します。

### 2. ローカルインストール管理

1. まずローカルインストール一覧を読み込みます。
2. `ローカル既存設定を更新` 相当の操作で可視状態を同期します。
3. 各インストール項目では次を扱えます。
   - `再インストール`
   - `アンインストール`
4. インストール操作は次を受け取ります。
   - `preflight`
   - `force_reinstall`
   - `source_preference=auto|uploaded_submission|generated`

### 3. Template アップロードフロー

1. `/member` のアップロード領域を開きます。
2. ファイルを選択するか、生成済み package を利用します。
3. template package の直接アップロード上限は `20 MiB` です。
4. upload オプション:
   - `scan_mode=strict|balanced`
   - `visibility=community|private`
   - `replace_existing=true|false`
5. 投稿後は `My Submissions` で詳細を確認し、自分の原本 package をダウンロードします。

### 4. Profile-Pack 投稿フロー

1. profile-pack artifact を準備し、`artifact_id` を取得します。
2. `/member` または `/market` から投稿します。
3. submit オプション:
   - `pack_type`
   - `selected_sections`
   - `redaction_mode`
   - `replace_existing`
4. 投稿後は `My Profile-Pack Submissions` で詳細と自分の export を確認します。

### 5. 能力ゲートとエラーモデル

1. ボタン単位の操作はすべて `/api/ui/capabilities` によってバックエンドポリシーからゲートされます。
2. 認証 / 制限 / 内部エラーは次の形で統一されます:
   `{"ok": false, "error": {"code": "...", "message": "..."}}`
3. owner 不一致は `permission_denied` を返します。
4. template アップロード超過は `package_too_large` を返します。
5. `prompt_injection_detected` のようなリスク検知は、無言削除ではなく審査シグナルとして表示されます。

## 公開 / 非公開の境界

1. 公開 docs は検索、インストール、アップロード、自分の投稿管理だけを扱います。
2. 審査操作、特権 apply/rollback、secret 処理、backup/restore SOP は公開しません。

## トラブルシューティング

1. `401`: 認証が有効で、現在の member 操作にログインが必要です。
2. `permission_denied`: 現在の token では対象 `user_id` または操作にアクセスできません。
3. `package_too_large`: template アップロードが `20 MiB` を超えました。
4. `prompt_injection_detected`: package は高リスクとしてマークされ、審査へ回されました。
5. ロケール表示が壊れた場合は `sharelife.uiLocale` を削除して再読込してください。
6. developer mode の状態が壊れた場合は `sharelife.developerMode` を削除して再読込してください。
