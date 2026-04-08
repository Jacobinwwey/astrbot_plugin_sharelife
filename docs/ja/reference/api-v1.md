# Sharelife API v1（公開 + member サーフェス）

このページでは、公開カタログ読み取り API と member 側の操作 API だけを扱います。
reviewer/admin/operator 向けのエンドポイントは公開リファレンスから外し、非公開運用ドキュメントへ移しました。

## 対象範囲

1. 公開読み取り API: マーケット検索、詳細、比較、ヘルス、能力確認。
2. member API: ログイン、トライアル、インストール、アップロード、profile-pack 投稿、ローカルインストール管理、自分の投稿一覧とダウンロード。
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
13. `list_profile_pack_catalog(pack_query="", pack_type="", risk_level="", review_label="", warning_flag="", featured="")`
14. `get_profile_pack_catalog_detail(pack_id)`
15. `compare_profile_pack_catalog(pack_id, selected_sections=None)`
16. `submit_profile_pack(user_id, artifact_id, submit_options=None)`
17. `list_member_installations(user_id, limit=50)`
18. `refresh_member_installations(user_id, limit=50)`
19. `uninstall_member_installation(user_id, template_id)`
20. `member_list_submissions(user_id, status="", template_query="", risk_level="", review_label="", warning_flag="")`
21. `member_get_submission_detail(user_id, submission_id)`
22. `member_get_submission_package(user_id, submission_id)`
23. `member_list_profile_pack_submissions(user_id, status="", pack_query="", pack_type="", risk_level="", review_label="", warning_flag="")`
24. `member_get_profile_pack_submission_detail(user_id, submission_id)`
25. `member_get_profile_pack_submission_export(user_id, submission_id)`

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
11. `POST /api/profile-pack/submit`
12. `GET /api/member/installations?user_id=...`
13. `POST /api/member/installations/refresh`
14. `POST /api/member/installations/uninstall`
15. `GET /api/member/submissions?user_id=...`
16. `GET /api/member/submissions/detail?user_id=...&submission_id=...`
17. `GET /api/member/submissions/package/download?user_id=...&submission_id=...`
18. `GET /api/member/profile-pack/submissions?user_id=...`
19. `GET /api/member/profile-pack/submissions/detail?user_id=...&submission_id=...`
20. `GET /api/member/profile-pack/submissions/export/download?user_id=...&submission_id=...`

## 公開アップロード / インストール payload

1. `POST /api/templates/install`
   - `install_options.preflight: bool`
   - `install_options.force_reinstall: bool`
   - `install_options.source_preference: auto|uploaded_submission|generated`
2. `POST /api/templates/submit`
   - `package_name + package_base64` による直接アップロード
   - `upload_options.scan_mode: strict|balanced`
   - `upload_options.visibility: community|private`
   - `upload_options.replace_existing: bool`
3. `POST /api/profile-pack/submit`
   - 現行 main では `artifact_id` が必須
   - `submit_options.pack_type: bot_profile_pack|extension_pack`
   - `submit_options.selected_sections: string[]`
   - `submit_options.redaction_mode: exclude_secrets|exclude_provider|include_provider_no_key|include_encrypted_secrets`
   - `submit_options.replace_existing: bool`
4. template パッケージの直接アップロード上限は `20 MiB` で、超過時は `package_too_large` を返します。

## Auth Badge Matrix (HTTP)

| ルート | 必要ロール | 拒否時の挙動 |
| --- | --- | --- |
| `GET /api/ui/capabilities` | `public` | N/A |
| `POST /api/login` | `public` | `401 invalid_credentials` または `429 rate_limited` |
| `GET /api/templates` | `public` | N/A |
| `GET /api/templates/detail` | `public` | N/A |
| `GET /api/profile-pack/catalog` | `public` | N/A |
| `GET /api/profile-pack/catalog/detail` | `public` | N/A |
| `GET /api/profile-pack/catalog/compare` | `public` | N/A |
| `GET /api/profile-pack/catalog/insights` | `public` | N/A |
| `POST /api/trial` | `member` または匿名 allowlist | `401 unauthorized` または `403 permission_denied` |
| `POST /api/templates/install` | `member` または匿名 allowlist | `401 unauthorized` または `403 permission_denied` |
| `POST /api/templates/submit` | `member` | `401 unauthorized` または `403 permission_denied` |
| `POST /api/profile-pack/submit` | `member` | `401 unauthorized` または `403 permission_denied` |
| `GET /api/member/installations` | `member` または匿名 allowlist | `401 unauthorized` または `403 permission_denied` |
| `POST /api/member/installations/refresh` | `member` または匿名 allowlist | `401 unauthorized` または `403 permission_denied` |
| `POST /api/member/installations/uninstall` | `member` | `401 unauthorized` または `403 permission_denied` |
| `GET /api/member/submissions` | `member` | `401 unauthorized` または `403 permission_denied` |
| `GET /api/member/submissions/detail` | `member` | `401 unauthorized` または `403 permission_denied` |
| `GET /api/member/profile-pack/submissions` | `member` | `401 unauthorized` または `403 permission_denied` |
| `GET /api/member/profile-pack/submissions/detail` | `member` | `401 unauthorized` または `403 permission_denied` |

ロール拒否系レスポンスはすべて `error.code=permission_denied` を返す前提です。

## エラーモデル

1. `permission_denied`: ロール不一致または owner バインディング違反。
2. `unauthorized` / `invalid_credentials`: ログイン必須または認証情報不正。
3. `package_too_large`: アップロードが `20 MiB` 上限を超過。
4. `template_not_installable`: 対象 template が現在インストール不可。
5. `profile_pack_source_required`: profile-pack 投稿時に `artifact_id` がない。
6. `prompt_injection_detected`: 高リスク信号を検知。現状はラベル付けと審査エスカレーションであり、自動削除ではありません。

## 実行時メモ

1. `get_trial_status()` と `GET /api/trial/status` は `not_started|active|expired` に加えて `ttl_seconds` と `remaining_seconds` を返します。
2. `GET /api/ui/capabilities` はログイン前でも読めるため、UI 側で保護操作を隠す / 無効化するための基点になります。
3. `allow_anonymous_member=true` を有効にした場合でも、匿名で使えるのは allowlist 内の API だけで、要求は `anonymous_member_user_id` に固定されます。
4. member のダウンロード面は owner スコープ前提です。自分の投稿物しかダウンロードできません。
5. 承認、apply/rollback、reviewer ライフサイクル、secret ローテーション、backup/restore、featured 運用は非公開 operator docs にのみ記載します。
