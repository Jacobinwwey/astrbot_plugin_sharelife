# Sharelife Market Center Entry 再設計 実装計画

> **Agentic worker 向け:** `superpowers:subagent-driven-development`（推奨）または `superpowers:executing-plans` を使い、この plan を task ごとに実行してください。step の tracking は checkbox（`- [ ]`）構文を使います。

**現在の言語:** 日本語

**対応ドキュメント:** 英語の基準版 `docs/superpowers/plans/2026-04-05-sharelife-market-center-redesign-implementation.md`、中国語版 `docs/superpowers/plans/2026-04-05-sharelife-market-center-redesign-implementation.zh-CN.md`

---

## 現在の実装ステータス

> 更新日: `2026-04-07`

この branch で完了している内容:

1. `/market` は public-first baseline で動作し、Spotlight search は sort row の上にあります。
2. public catalog refresh button は `Refresh Catalog` に統一されました。
3. public search は localized alias を含み、`官方` のような中国語 query でも official pack を解決できます。
4. public catalog card には local like control と visible like count を追加しました。
5. member-side local installation management は refresh / reinstall / uninstall を備えています。
6. backend には `member.installations.uninstall` が追加され、local installation visibility は最新 install / uninstall audit event に基づきます。

現在の verification メモ:

1. source-level tests は green です。
2. browser E2E をこの環境で実行するには local `playwright` Node dependency が必要です。

---

### 説明

この file は implementation plan の日本語独立版です。EN / 中文 / 日本語 を同一 file に混在させず、locale ごとに管理する i18n 方針に合わせます。

実行コマンド、code block、file path、commit command は実行誤差を避けるため英語原文を残し、ここではタスクの目的、file の責務、step の意味、verification 要件を日本語で補います。

### ゴール

`/market` を public-read-only 優先の market entry に作り直します。

1. first screen は browse と search が中心
2. card は public fact のみを見せる
3. member action は card click 後の detail drawer / sheet に集約する
4. 後続の Stitch-generated 5 variant も detail layer のみを対象にする

### アーキテクチャ概要

基本方針:

1. existing standalone `/market` route を維持
2. vanilla WebUI stack を継続利用
3. `market_page.js` にこれ以上責務を積み増さない
4. public catalog contract と detail-shell contract の 2 つの helper boundary を切り出す
5. runtime ID は可能な限り維持する
6. Stitch pre-call gate のために `sharelife/webui/market_detail/` と module-local `Design.md` を用意する

### ファイル構成

#### 新規作成

- `sharelife/webui/market_catalog_contract.js`
  public card view model、search text、detail seed payload を担当。
- `sharelife/webui/market_detail/detail_shell.js`
  drawer / sheet mode、member-action gating、default detail state を担当。
- `sharelife/webui/market_detail/variant_registry.js`
  variant ID、active variant normalization、renderer lookup を担当。
- `sharelife/webui/market_detail/Design.md`
  detail layer 用 module-local Stitch source-of-truth。
- `sharelife/webui/market_detail/variants/variant_1.js` から `variant_5.js`
  5 つの detail variant renderer。
- `tests/meta/test_market_center_surface.py`
  public-first market HTML surface を検証。
- `tests/webui/test_market_catalog_contract.js`
  public card / search / detail-seed helper を検証。
- `tests/webui/test_market_detail_shell.js`
  detail shell と member-action gate を検証。
- `tests/webui/test_market_detail_variants.js`
  variant ID、switching、renderer registration を検証。

#### 修正

- `sharelife/webui/market.html`
  header -> Spotlight search -> result controls に再配置し、detail-shell placeholder を追加。
- `sharelife/webui/market_page.js`
  public catalog contract を接続し、detail shell、member action、variant switching を載せる。
- `sharelife/webui/style.css`
  Spotlight search、public-entry hierarchy、drawer / sheet detail-shell style を追加。
- `sharelife/webui/webui_i18n.js`
  market entry / detail / variant 用の EN / 中文 / 日本語 copy を追加。
- `docs/superpowers/specs/2026-04-05-market-center-redesign-design.ja-JP.md`
  実装により本当の spec contradiction が見つかった時のみ更新。

#### Export Rule

新しい browser helper は current WebUI の dual-export pattern を守ります。

1. `module.exports` を `node:test` 用に出す
2. `globalScope.<Name>` を browser runtime 用に出す

#### 変更しないもの

- `sharelife/webui/market_cards.js`
  この slice では拡張せず、新 public catalog logic は `market_catalog_contract.js` に置く。

### タスク概要

#### Task 1: Public-First Market Surface を固定する

主目的:

1. surface test で public-first skeleton を先に固定
2. `market.html` から first-screen member operation block を除去
3. detail shell container を追加

主な確認:

1. `marketGlobalSearch` が `marketSortBy` より前にある
2. first screen に `btnMarketRefreshInstallations` がない
3. `marketDetailVariantTabs` が存在する
4. `marketDetailMemberActions` が存在する

#### Task 2: Public Catalog Contract を抽出する

主目的:

1. public card contract を page script から分離
2. primary action を `open_detail` のみにする
3. search text と detail seed を独立して test 可能にする

主な確認:

1. public card に member action を表示しない
2. search text が主要 public metadata を含む
3. detail seed が stable な pack context を返す

#### Task 3: Detail-Shell 境界と Stitch Source File を作る

主目的:

1. detail shell の module boundary を分離
2. module-local `Design.md` を先に作る
3. 後続 Stitch call の source-of-truth を明確化

主な確認:

1. drawer / sheet mode 判定が独立している
2. member action を起こす前には auth を要求しない
3. variant switch 中も pack context が安定している

#### Task 4: Member Action を Detail Shell の後ろへ移動する

主目的:

1. first screen から install / upload / trial を除去
2. detail layer のみで member action を見せる
3. 実行時 auth gate を維持する

主な確認:

1. first-screen browsing と member action の境界が明確
2. detail shell が action を受けられる
3. login は実際の action 実行時だけ必要

#### Task 5: Spotlight Hierarchy と三言語 copy を適用する

主目的:

1. Spotlight 風 search を first screen の main visual anchor にする
2. result controls の位置と hierarchy を整える
3. EN / 中文 / 日本語 copy を揃える

主な確認:

1. search box が entry header の下、sort row の上にある
2. first screen が public market として読める
3. 3 言語で core copy が正しく表示される

#### Task 6: Stitch 前に Variant Registry を完成させる

主目的:

1. 5 variant の stable switching shell を先に用意
2. Stitch output が来る前に registry を固める
3. same pack context のまま one-click switching を可能にする

主な確認:

1. `variant_1` から `variant_5` が stable ID
2. invalid input が normalize される
3. renderer registration が拡張可能

#### Task 7: `Design.md` を確定し、Stitch を実行して 5 variant を統合する

主目的:

1. detail-layer `Design.md` を finalize
2. その後で Stitch call を実行
3. 少なくとも 5 つの compare 可能な variant を取得
4. 5 分待ってから取得
5. runtime shell に統合

主な確認:

1. 5 variant が same pack context で切り替わる
2. public facts / member actions / auth gate が壊れない
3. 旧 market hub の visual language に戻らない

### 最終検証

最後に確認する内容:

1. 関連 `node --test` WebUI test
2. 関連 `pytest` surface test
3. 必要なら docs/private index refresh
4. `/market`、detail shell、variant switching、三言語 copy、docs portal の visual check
