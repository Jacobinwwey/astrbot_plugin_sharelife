# 2026-04-06 v1.2 - Sharelife Market Center Entry 再設計

## 時刻とバージョン

- 日付: 2026-04-06
- バージョン: v1.2
- ステータス: implementation baseline 向けに更新済み
- 現在の言語: 日本語
- 対応ドキュメント:
  - 英語の基準版: `docs/superpowers/specs/2026-04-05-market-center-redesign-design.md`
  - 中国語版: `docs/superpowers/specs/2026-04-05-market-center-redesign-design.zh-CN.md`

### コンテキスト

`/market` はすでに standalone な Sharelife WebUI route として存在していますが、現状の page は 2 つの job を混在させています。

1. public catalog browsing
2. member 側の trial、install、submit、local-state operation

この構成は両面で弱く、public market entry として読みづらく、browse だけしたいユーザーにとって first screen が必要以上に重くなっています。

ユーザーが求めた product constraint は次の通りです。

1. fresh clone と clean branch で作業する
2. `/market` を primary slice として扱う
3. first screen を public-read-only first にする
4. member action を card-click 後の detail layer に移す
5. first slice では always-on compare を作らない
6. high-density console の reference direction は使うが、information hierarchy は作り直す
7. 後段では Stitch MCP を使って少なくとも 5 つの detail-layer variant を生成し、5 分待ってから取得し、one-click で比較可能にする

### ゴール

`/market` を、browse と discovery を最優先にした明確な public market entry に変えつつ、特定 pack を開いた後には authenticated member action へ clean に handoff できるようにすることです。

### スコープ

この design が扱う範囲:

1. standalone `/market` page の information architecture
2. public catalog grid の card-level contract
3. card click 後に member action を保持する detail-layer contract
4. hand-built market entry と後続 Stitch detail variant の staged execution boundary
5. 既存 runtime ID、API wiring、test を保つための key constraint

この design が扱わない範囲:

1. 同一 slice での `/`、`/member`、`/admin` の同時 refactor
2. first slice で always-on compare を戻すこと
3. UI contract を block しない限り backend market API を再設計すること
4. Stitch generation 前の final detail visual の確定
5. 永続的な新 ranking system、personalization、favorites flow

### 検討したアプローチ

#### Approach A: Editorial public hub

利点:

1. public landing page 感が最も強い
2. featured pack と trust messaging を強調しやすい

欠点:

1. dense な catalog browsing には弱い
2. 既存 market-page structure から離れすぎる
3. first slice に対して layout churn が大きい

#### Approach B: Curated catalog console

利点:

1. reference direction と current `/market` code shape に最も合う
2. high-density browsing を保ちながら action boundary を整理できる
3. list layer が安定するため、後続の Stitch detail-layer work がやりやすい

欠点:

1. public market として読めるよう careful な hierarchy 調整が必要

#### Approach C: Hybrid landing plus results

利点:

1. pure console より強い brand statement を出せる
2. trust や review-process messaging を前面に出しやすい

欠点:

1. first screen が重くなる
2. search と browsing efficiency が薄まる危険がある
3. first slice の redesign cost が高い

### 決定

Approach B: curated catalog console を採用します。

standalone market page は efficient な catalog-console structure を維持しつつ、意味づけを「mixed operations dashboard」から「public market entry」へ切り替えます。public browsing を first-screen の主要 job にし、member action は card-open detail layer の後ろに移します。

### デザイン

#### 1. Entry Positioning

`/market` は Sharelife market の public-read-only front door になります。

初期表示で強調すべき内容:

1. Sharelife Market とは何か
2. どう browse するか
3. なぜ catalog を trust できるか

初期表示で強調しない内容:

1. local installation state refresh
2. 直ちに行う install / upload action
3. pack 選択前の role-specific operation

#### 2. Information Architecture

catalog result の上には 3 層の stacked layer を置きます。

1. brand と context header
2. Spotlight-style global search
3. result controls

その下の main catalog area は 2 カラムを維持します。

1. compact な left filter rail
2. right-side の card grid

#### 3. Header Layer

header layer は current top utility bar より slim で public tone に寄せます。

含める内容:

1. `Sharelife` brand mark と market title
2. short な public-market positioning line
3. locale switch
4. documentation link とその他 public-read-only link

first screen から remove または demote する内容:

1. `Refresh Local Installations`
2. member / admin operation の強調
3. upload / install / trial CTA

cross-console link を残す場合も primary action ではなく secondary navigation として扱います。

#### 4. Spotlight-Style Search Layer

search field は page 全体の main visual anchor になります。

配置:

1. main entry header の直下
2. sort / results row の上
3. utility-table filter input ではなく Spotlight や Raycast に近い広さ

振る舞い:

1. floating overlay ではなく in-page 埋め込み
2. `pack_id`、title-like label、maintainer、tags、review labels、warning flags、compatibility、利用可能な summary text を対象に検索
3. visible grid を更新するだけで、page を auth-first workflow に変えない

product intent:

1. discovery を primary に感じさせる
2. page が operation console first に見える印象を弱める

#### 5. Result Controls Layer

search field の下の row は result-navigation control のみを載せます。

残すもの:

1. sort choice
2. result count
3. 現在の code が clean に対応している場合のみ optional view toggle

混ぜないもの:

1. install action
2. upload action
3. auth-first control
4. local installation refresh

refresh affordance を残す場合も catalog refresh として再定義し、local-installation refresh とは読ませません。

#### 6. Filter Rail

left rail は selected console direction と existing page structure に合うため維持します。

public browsing filter に限定する対象例:

1. pack type
2. risk level
3. compatibility
4. featured state
5. review labels
6. warning flags

member operation 用の第 2 control panel にはしません。

#### 7. Catalog Card Contract

public card layer は「この pack は何で、どのくらい risk があり、詳細を開く価値があるか」という狭い問いに答えるべきです。

各 card で公開する public-read-only metadata:

1. pack identifier または display title
2. pack type
3. version
4. maintainer
5. compatibility status
6. risk level
7. short summary
8. 少数の tags と review / warning indicator
9. section count、label count、update recency などの lightweight metric

card layer に直置きしない action:

1. Try
2. Install
3. Upload
4. Member login や local environment check

primary action は detail-opening affordance に限定します。

1. card 全体クリック
2. `View Details` button クリック

#### 8. Detail-Layer Contract

card を開くと second-layer surface に移るべきです。

default form:

1. desktop は right-side detail drawer
2. mobile は full-screen sheet

この層で初めて deeper information と member action を見せます。

ここで初めて見せる内容:

1. Try
2. Install
3. upload-related action / link
4. member-only environment notice
5. 必要なら authentication prompt
6. protected install 実行前の section-sync choice

public detail content は login 前でも読める状態を維持します。auth は try、install、upload 関連など実際の member action が起きた時だけ要求します。

Install は detail layer 内で section-selective sync をサポートしなければなりません。`memory_store`、`conversation_history`、`knowledge_base` のような stateful / local-data section は optional sync target として表現し、ユーザーが意図的に skip できるようにします。

detail layer が利用する stable data contract:

1. `pack_id`
2. display title があれば利用
3. `version`
4. `maintainer`
5. `pack_type`
6. `risk_level`
7. `compatibility`
8. `review_labels`
9. `warning_flags`
10. `sections`
11. summary または description
12. updated-at style metadata
13. API が返す public audit / source fact

後で Stitch により visual layout が変わっても、この contract は安定したままにします。

#### 9. Two-Phase Delivery

##### Phase 1: Hand-built public entry refactor

実装する内容:

1. header rewrite
2. Spotlight-style search placement
3. clean な result-controls row
4. public-only filter rail
5. public card contract
6. click-to-open detail-layer shell

この phase で実装しない内容:

1. always-on compare
2. final 版の high-design detail variant
3. 他 WebUI page への broad refactor

##### Phase 2: Stitch-generated detail variants

main entry と detail-layer contract が stable になった後、detail layer のみを対象に Stitch MCP を使います。

first-screen の market entry は hand-integrated な production HTML / CSS / JS のまま維持し、variant exploration の対象は detail layer に限定します。

#### 10. Stitch Generation Rules

detail-layer generation step では次の rule に従います。

1. 1 回の target で少なくとも 5 variant を生成する
2. 5 variant は同じ detail-layer job を表し、無関係な screen 群にしない
3. Stitch generation call 後は 5 分待ってから取得する
4. suggestion-style output が返っても follow-up path を受け入れつつ、少なくとも 5 usable variant に到達する
5. single opened pack context の中で easy に compare できるようにする
6. generated detail direction は install-time section sync choice を表現できる余地を残し、全 declared section が mandatory だと読める構図にしない

production requirement は「5 つの dead-end mockup」ではなく、「1 つの detail layer に対する 5 つの比較可能な option」です。

推奨 affordance:

1. `Variant 1` 〜 `Variant 5` の segmented control あるいは tab strip
2. same pack context を保持したまま detail presentation だけを切り替える

##### Stitch MCP Pre-Call Gate

この slice で Stitch MCP call を行う前に、次の前提を必ず満たします。

1. exact target 向けの improved Stitch MCP instruction set を先に確定する
2. その instruction set を chat history のみに置かず、module-local `Design.md` に書き込む
3. `Design.md` は Stitch-generated surface を所有する frontend adjustment module の独立 folder 配下に置く
4. この market-center slice では Stitch-owned target は first-screen market entry ではなく detail layer
5. module-local `Design.md` に最低限記録する内容:
   1. target surface と user job
   2. required data contract
   3. break してはいけない DOM / runtime constraint
   4. finalized Stitch MCP prompt / instruction block
   5. expected variant count と compare behavior
   6. generation 後の acceptance check
   7. 最新承認済み market-center baseline と current install-time section-sync rule
6. この `Design.md` が存在し review 済みになるまで、実際の Stitch generation call を行わない

#### 11. Preserve すべき Runtime Constraint

refactor は可能な限り current architecture を維持します。

1. `/market` は existing standalone route のまま維持
2. focused split が必要でない限り `market.html`、`market_page.js`、`market_cards.js`、`style.css` を再利用
3. current JS と test が依存する DOM ID や hook を不用意に壊さない。rename するなら test-backed にする
4. current WebUI i18n behavior と整合させる
5. runtime catalog data と public snapshot data の source strategy を維持する

#### 12. リスク

主要リスク:

1. 古い action がなお visual 優位だと page が operation-heavy に見え続ける
2. search が pack ID のみを対象にすると探索深度が不足する
3. detail layer が temporary hand-built layout に過度結合すると、後続 Stitch replacement の cost が上がる
4. 必要な ID や container を外すと current JS binding が壊れる

緩和策:

1. first screen から high-priority member action を外す
2. search field を事前に明確化して test する
3. detail layer を「stable data contract + replaceable presentation layer」として扱う
4. production code を触る前に focused な WebUI test を追加する

#### 13. テスト戦略

production code を変更する前に、次を追加または拡張します。

1. 新しい public card contract を支える market card view-model behavior
2. 選定 metadata field を使う search behavior
3. first-screen public browsing と detail-layer member action の boundary
4. Stitch visual が入る前の detail-layer state と variant-switching shell

visual verification で確認する内容:

1. search box が最も強い visual anchor になっていること
2. first screen が member operation page ではなく public catalog として読めること
3. card 上に install / trial / upload action が直接露出していないこと
4. card click が deeper action layer への明確な entry になっていること

### 成功基準

次を満たした時、この redesign slice は完了です。

1. `/market` の first screen が public read-only market entry として読める
2. Spotlight-style global search が entry header の下、sort row の上にある
3. first screen は browse / filter / search を支えつつ、card に member action を直接出さない
4. card click 後に、member action を受ける stable な detail-layer shell が開く
5. detail-layer contract が十分 stable で、後続 Stitch generation のために list layer を書き換える必要がない
6. 後続 Stitch step で少なくとも 5 detail variant を生成でき、one-click compare を支えられる
