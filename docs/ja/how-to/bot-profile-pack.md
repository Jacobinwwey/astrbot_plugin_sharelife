# Bot Profile Pack 運用

このページは公開 / member 向けに、profile-pack の閲覧、比較、投稿フローだけを扱います。
特権承認、featured 運用、secret export ルール、復旧手順は公開ドキュメントでは扱いません。

移行境界の真値表を先に確認したい場合は、こちらを参照してください:
[Bot 設定移行スコープ](/ja/how-to/profile-pack-migration-scope)

## 現在 member ができること

1. `/market` で公開済み profile-pack を閲覧する。
2. `Detail & Compare` で section 単位の runtime 比較を行う。
3. member 側から profile-pack artifact をコミュニティ投稿する。
4. 自分の profile-pack 投稿だけを一覧表示する。
5. 自分の投稿 export だけをダウンロードする。

## 公式リファレンス pack

Sharelife は次の starter pack を自動で供給します。

1. `pack_id`: `profile/official-starter`
2. `pack_type`: `bot_profile_pack`
3. `version`: `1.0.0`
4. `featured`: `true`

用途:

1. カタログ絞り込みの基準 (`pack_id=profile/official-starter`)
2. runtime 比較の予行演習
3. 投稿前に `selected_sections` を検証する基準

## 現在の member 投稿フロー

1. ローカルで profile-pack artifact を用意し、`artifact_id` を取得します。
2. ローカル WebUI の `/member` または `/market` を開きます。
3. profile-pack エリアで `artifact_id` を `コミュニティへ投稿` に入力します。
4. 任意の submit オプション:
   - `pack_type`
   - `selected_sections`
   - `redaction_mode`
   - `replace_existing`
5. 投稿後は `My Profile-Pack Submissions` で状態、詳細、自分の export を確認します。

## 投稿オプション

1. `pack_type`
   - `bot_profile_pack`
   - `extension_pack`
2. `selected_sections`
   - 今回公開する section の絞り込み
3. `redaction_mode`
   - `exclude_secrets`
   - `exclude_provider`
   - `include_provider_no_key`
   - `include_encrypted_secrets`
4. `replace_existing`
   - 同じ member + pack の古い pending 投稿を `replaced` に寄せ、最新の pending 投稿を審査対象として残します

## 比較とローカル適用の境界

1. 公開 / member docs は比較と投稿だけを扱います。
2. 特権 apply/rollback は公開契約に含めません。
3. 現在の推奨フロー:
   - 公開済み pack を閲覧する
   - section 単位で比較する
   - ローカル導入の可否を判断する
   - 公開したい場合だけ自分の artifact を投稿する

## 現在の制約

1. 現在の main ではコミュニティ投稿は `artifact_id` ベースであり、公開 ZIP 直接アップロードは契約に含めません。
2. `replace_existing` は pending 行の整理だけで、承認済み / 却下済みの履歴は上書きしません。
3. 比較 / 投稿の結果は「完全復元点」を意味しません。助言的な比較結果であり、完全な環境スナップショット復元ではありません。
4. secret を含む operator export は公開 artifact にならず、member docs 側からもダウンロードできません。

## ユーザー可視ステータス

1. `pending`
2. `approved`
3. `rejected`
4. `replaced`

## セキュリティ境界

1. profile-pack catalog ルートは公開読み取り専用です。
2. 投稿と「自分の投稿」ルートは member 専用で、owner スコープです。
3. 特権審査、device/session ガバナンス、高権限ストレージ運用は非公開 docs のみで扱います。
