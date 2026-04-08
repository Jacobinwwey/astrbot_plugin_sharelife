# 公開マーケット（読み取り専用）

このページはマーケット公開面の境界を定義します。

## 目的

1. 利用可能な公開カタログを提供する。
2. 特権実行はローカルに閉じる。
3. ユーザーをローカル WebUI へ自然に引き渡し、導入や投稿を行わせる。

## 関連ページ

[マーケットカタログ試作ページ](/ja/how-to/market-catalog-prototype)

## 公開ページに含めてよいもの

1. template/profile-pack のメタデータ
2. リスクラベルと互換性メモ
3. Detail + Compare 表示
4. ダウンロード / 導入ガイダンス
5. ロケール別テキスト（`ja` / `en` / `zh`）
6. サニタイズ済みの公式 / コミュニティ artifact

## 公開ページに含めてはいけないもの

1. moderation の決裁操作
2. 特権 apply/rollback 操作
3. 特権認証や secret 管理
4. operator 向け backup/restore 手順
5. featured 運用コントロール

## 現在の公開面

`2026-04-07` 時点で、公開マーケットは次を満たす想定です。

1. Spotlight 形式の検索が最初の操作になる。
2. カタログカードは公開読み取り専用のままにする。
3. `Detail & Compare` は pack 選定と section 判断のために表示できる。
4. 保護された member 操作はローカル `/member` または `/market` に残し、公開ファーストビューには戻さない。

## ローカル WebUI への受け渡し

1. まず公開ハブで閲覧する。
2. 次にローカル Sharelife WebUI を開く。
3. 保護操作は `/member` または `/market` で行う。
4. 認証が有効なら `member` としてログインする。
5. ローカルでは次のいずれかへ進む。
   - `preflight` / `force_reinstall` / `source_preference` 付きインストール
   - `scan_mode` / `visibility` / `replace_existing` 付き template アップロード
   - `artifact_id` と `submit_options` を使う profile-pack 投稿
6. 結果は member スコープの投稿一覧で追跡する。

## アップロードチェーンのメモ

1. template package アップロード上限は `20 MiB` です。
2. profile-pack のコミュニティ投稿は、現行 main では `artifact_id` ベースです。
3. 公開ページでは引き渡し方は説明できますが、特権 operator 操作は露出してはいけません。

## ロケール基線

1. 公開 docs は現在のルートロケールを基準にします。
2. 公開ページをローカル operator 状態に結び付けません。
3. `/ja`、`/en`、`/zh` で同じ境界語彙を保ちます。

## 招待制ロール

1. 公開ページは review や運用コントロールを露出しません。
2. 招待制の review 権限が必要な場合は `Jacobinwwey` に連絡してください。
