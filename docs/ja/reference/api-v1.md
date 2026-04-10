# Sharelife API v1（公開 + member サーフェス）

このページでは、公開カタログ読み取り API と member 側の操作 API だけを扱います。
特権付きの内部エンドポイントは公開リファレンスでは扱いません。

## 対象範囲

1. 公開読み取り API: マーケット検索、詳細、比較、ヘルス、能力確認。
2. member API: ログイン、トライアル、インストール、アップロード、profile-pack の import/投稿、ローカルインストール管理、タスク復元、transfer-job 可視化、自分の投稿一覧とダウンロード。
3. owner バインディング: 認証有効時、member ルートは現在の認証 `user_id` に属するデータだけを操作できます。

## 公開 + member アプリケーションメソッド

1. `get_preferences(user_id)`
2. `set_preference_mode(user_id, mode)`
3. `set_preference_observe(user_id, enabled)`
4. `submit_template(user_id, template_id, version)`
5. `submit_template_package(user_id, template_id, version, filename, content_base64)`
6. `list_templates()`
7. `get_template_detail(template_id)`
8. `request_trial(user_id, session_id, template_id)`
9. `get_trial_status(user_id, session_id, template_id)`
10. `install_template(user_id, session_id, template_id)`
11. `generate_prompt_bundle(template_id)`
12. `generate_package(template_id)`
13. `list_member_tasks(user_id, limit=50)`
14. `refresh_member_tasks(user_id, limit=50)`
15. `list_member_transfer_jobs(user_id, direction="", status="", limit=50)`
16. `refresh_member_transfer_jobs(user_id, direction="", status="", limit=50)`
17. `list_profile_pack_catalog(pack_query="", pack_type="", risk_level="", review_label="", warning_flag="", featured="")`
18. `get_profile_pack_catalog_detail(pack_id)`
19. `compare_profile_pack_catalog(pack_id, selected_sections=None)`
20. `member_import_profile_pack(user_id, filename, content_base64)`
21. `member_list_profile_pack_imports(user_id, limit=50)`
22. `submit_profile_pack(user_id, artifact_id, submit_options=None)`
23. `list_member_installations(user_id, limit=50)`
24. `refresh_member_installations(user_id, limit=50)`
25. `uninstall_member_installation(user_id, template_id)`
26. `member_list_submissions(user_id, status="", template_query="", risk_level="", review_label="", warning_flag="")`
27. `member_get_submission_detail(user_id, submission_id)`
28. `member_get_submission_package(user_id, submission_id, idempotency_key="")`
29. `member_list_profile_pack_submissions(user_id, status="", pack_query="", pack_type="", risk_level="", review_label="", warning_flag="")`
30. `member_get_profile_pack_submission_detail(user_id, submission_id)`
31. `member_withdraw_profile_pack_submission(user_id, submission_id)`
32. `member_get_profile_pack_submission_export(user_id, submission_id)`

## 公開 + member HTTP ルート

公開ルート:

1. `GET /api/auth-info`
2. `POST /api/login`
3. `GET /api/health`
4. `GET /api/ui/capabilities?page_mode=auto|member|market`
5. `GET /api/templates`
6. `GET /api/templates/detail?template_id=...`
7. `GET /api/profile-pack/catalog`
8. `GET /api/profile-pack/catalog/detail?pack_id=...`
9. `GET /api/profile-pack/catalog/compare?pack_id=...&selected_sections=plugins,providers`
10. `GET /api/profile-pack/catalog/insights`

member ルート:

1. `GET /api/preferences?user_id=...`
2. `POST /api/preferences/mode`
3. `POST /api/preferences/observe`
4. `POST /api/trial`
5. `GET /api/trial/status?user_id=...&session_id=...&template_id=...`
6. `POST /api/templates/install`
7. `POST /api/templates/submit`
8. `GET /api/templates/package/download?template_id=...`
9. `POST /api/templates/prompt`
10. `POST /api/templates/package`
11. `GET /api/member/tasks?user_id=...`
12. `POST /api/member/tasks/refresh`
13. `GET /api/member/transfers?user_id=...&direction=download&status=...`
14. `POST /api/member/transfers/refresh`
15. `POST /api/profile-pack/submit`
16. `POST /api/member/profile-pack/imports`
17. `GET /api/member/profile-pack/imports?user_id=...`
18. `GET /api/member/installations?user_id=...`
19. `POST /api/member/installations/refresh`
20. `POST /api/member/installations/uninstall`
21. `GET /api/member/submissions?user_id=...&status=...&template_id=...&risk_level=...`
22. `GET /api/member/submissions/detail?user_id=...&submission_id=...`
23. `GET /api/member/submissions/package/download?user_id=...&submission_id=...`
24. `GET /api/member/profile-pack/submissions?user_id=...&status=...&pack_id=...&pack_type=...`
25. `GET /api/member/profile-pack/submissions/detail?user_id=...&submission_id=...`
26. `POST /api/member/profile-pack/submissions/withdraw`
27. `GET /api/member/profile-pack/submissions/export/download?user_id=...&submission_id=...`

## 公開アップロード / インストール payload メモ

1. `POST /api/templates/install`
   - `install_options.preflight: bool`
   - `install_options.force_reinstall: bool`
   - `install_options.source_preference: auto|uploaded_submission|generated`
2. `POST /api/templates/submit`
   - `package_name + package_base64` による直接パッケージ投稿
   - `upload_options.scan_mode: strict|balanced`
   - `upload_options.visibility: community|private`
   - `upload_options.replace_existing: bool`
   - `upload_options.idempotency_key` または `Idempotency-Key` ヘッダーによる安全な再試行
3. `POST /api/profile-pack/submit`
   - 現在ブランチでは `artifact_id` が必須
   - `submit_options.pack_type: bot_profile_pack|extension_pack`
   - `submit_options.selected_sections: string[]`
   - `submit_options.redaction_mode: exclude_secrets|exclude_provider|include_provider_no_key|include_encrypted_secrets`
   - `submit_options.replace_existing: bool`
   - `submit_options.idempotency_key` または `Idempotency-Key` ヘッダーによる安全な再試行
4. `POST /api/member/profile-pack/imports`
   - `filename + content_base64` で、コミュニティ投稿前の member 所有 import draft を作成
5. `GET /api/member/submissions/package/download`
   - 任意の `Idempotency-Key` ヘッダーで重複 download job 生成を抑止
   - 成功レスポンスに `X-Sharelife-Transfer-Job-Id` と `X-Sharelife-Transfer-Status` が付く場合がある
6. 直接テンプレートアップロードは `20 MiB` 上限で、超過時は `package_too_large` を返します。

## Auth Badge Matrix (HTTP)

| Route | Required Role | Deny Behavior |
| --- | --- | --- |
| `GET /api/ui/capabilities` | `public` | N/A |
| `POST /api/login` | `public` | `401 invalid_credentials` or `429 rate_limited` |
| `GET /api/templates` | `public` | N/A |
| `GET /api/templates/detail` | `public` | N/A |
| `GET /api/profile-pack/catalog` | `public` | N/A |
| `GET /api/profile-pack/catalog/detail` | `public` | N/A |
| `GET /api/profile-pack/catalog/compare` | `public` | N/A |
| `GET /api/profile-pack/catalog/insights` | `public` | N/A |
| `POST /api/trial` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `POST /api/templates/install` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `GET /api/templates/package/download` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `GET /api/notifications` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/tasks` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/tasks/refresh` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/transfers` | `member` | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/transfers/refresh` | `member` | `401 unauthorized` or `403 permission_denied` |
| `POST /api/templates/submit` | `member` | `401 unauthorized` or `403 permission_denied` |
| `POST /api/profile-pack/submit` | `member` | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/profile-pack/imports` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/profile-pack/imports` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/installations` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/installations/refresh` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/installations/uninstall` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/submissions` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/submissions/detail` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/submissions/package/download` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/profile-pack/submissions` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/profile-pack/submissions/detail` | `member` | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/profile-pack/submissions/withdraw` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/profile-pack/submissions/export/download` | `member` | `401 unauthorized` or `403 permission_denied` |

All role-deny responses are expected to return `error.code=permission_denied`.

## Error Model

1. `permission_denied`：ロールまたは owner binding により現在の操作が拒否される。
2. `unauthorized` / `invalid_credentials`：ログインが必要、または資格情報が不正。
3. `package_too_large`：アップロードパッケージが `20 MiB` 上限を超過。
4. `template_not_installable`：対象テンプレートが現在インストール不可。
5. `profile_pack_source_required`：profile-pack 投稿時に `artifact_id` が未指定。
6. `idempotency_key_conflict`：同じ冪等キーが別スコープの投稿に再利用された。
7. `prompt_injection_detected`：スキャンが高リスク信号を検出。現行動作はラベル付与と審査エスカレーションであり、自動削除ではない。

## 実行時メモ

1. `get_trial_status()` と `GET /api/trial/status` は `not_started|active|expired` に加え `ttl_seconds` / `remaining_seconds` を返す。
2. `GET /api/ui/capabilities` はログイン前でも読み取り可能で、UI はこれを元に保護操作の表示・無効化を切り替える。
3. `allow_anonymous_member=true` の場合でも、匿名実行できるのは allowlist の操作だけで、要求は `anonymous_member_user_id` に固定される。
4. `GET /api/templates` は `category`、`tag`、`source_channel`、`review_label`、`warning_flag`、`sort_by`、`sort_order` によるサーバー側フィルタ/ソートをサポートする。
5. テンプレート一覧と詳細 payload は `category`、`tags`、`maintainer`、`source_channel`、および市場ランキング用の `engagement` 集約を返す。
6. 現在の `engagement` には `trial_requests`、`installs`、`prompt_generations`、`package_generations`、`community_submissions`、`last_activity_at` が含まれる。
7. `POST /api/templates/submit` と `POST /api/profile-pack/submit` は payload オプションまたは `Idempotency-Key` ヘッダーによる冪等リプレイに対応する。
8. member タスクルートはページ再読込後でも upload/download 履歴を監査イベントから復元する。
9. member transfer ルートは `attempt_count`、`retry_count`、`failure_reason`、`metadata` を返し、download トラブルシュートに使える。
10. 投稿パッケージ download は transfer-job 情報を payload とレスポンスヘッダーへ付加でき、同一 logical download の安全な再実行に使える。
11. member profile-pack import は、コミュニティ投稿されるまで member 所有の draft として保持される。
12. `POST /api/member/profile-pack/submissions/withdraw` により、pending 投稿がキュー処理に入る前に取り下げできる。
13. member ダウンロード系は owner scope を強制するため、自分の投稿物だけを取得できる。
14. 承認、apply/rollback、secret rotation、backup/restore、featured 運用などの特権フローは公開ドキュメントセットの対象外。
