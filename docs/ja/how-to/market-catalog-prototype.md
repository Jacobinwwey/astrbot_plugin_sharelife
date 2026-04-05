# マーケットカタログ試作ページ

このページは Sharelife マーケットカタログの読み取り専用プロトタイプです。  
コミュニティ向けの発見導線と UI 検証に特化し、権限操作は含みません。

## 対象範囲

1. 公開 profile-pack 向けのローカルフィルタ（pack type / risk / featured / review label）。
2. `source_channel`、`compatibility`、`maintainer`、ダウンロード導線を含む高密度カード表示。
3. ダウンロードリンクは脱敏済みの公開 profile-pack 成果物のみを指します。
4. 行データは公開スナップショット（`/market/catalog.snapshot.json`）を優先し、失敗時は内蔵デモ行へフォールバックします。

## プロトタイプ

<MarketCatalogPrototype locale="ja" />

## 補足

1. 本ページは読み取り専用ですが、データ供給は純ハードコードではありません。
2. `docs/public/market/catalog.snapshot.json` をデータソースにし、スナップショット未取得時のみ内蔵デモ行へフォールバックします。
3. レビュー・import/apply はローカル Sharelife WebUI の管理系で実施します。
4. 将来サーバ駆動の catalog に移行しても、同じテーブル構造を再利用できます。
5. UI 文言は `zh`/`en`/`ja` の辞書から描画し、ハードコードによる言語混在を避けます。
6. この試作ページはルート/ページ単位の locale（`<MarketCatalogPrototype locale=\"...\">`）を使い、ブラウザ保存値 `sharelife.uiLocale` は参照しません。
7. スタンドアロン WebUI 側の locale 永続化とフォールバックは [スタンドアロン WebUI](/ja/how-to/webui-page) を参照してください。
8. スナップショットと公開成果物は、公式サンプル pack と `docs/public/market/entries/*.json` を元に `npm run docs:prepare:market --prefix docs` で再生成されます（`docs:build` 実行時に自動実行）。
9. runtime 比較の可視化カード・セクション差分表・警告ハイライトはローカル WebUI 側（メイン画面の profile-pack market セクションと独立 `/market`）で提供し、本公開読み取り専用プロトタイプには含めません。
