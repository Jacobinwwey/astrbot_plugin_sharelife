# 2026-04-06 v2.1 - Sharelife Market Detail Layer Stitch 設計メモ

## メタ情報

- 日付: 2026-04-06
- バージョン: v2.1
- ステータス: current Stitch baseline を確認済み、5 variants の再生成を送信済み
- 注記: 実際の Stitch call で使う canonical prompt source は `Design.md`

## 対象サーフェスとユーザージョブ

対象は `/market` カードから開く detail layer です。

ユーザージョブ:

1. 選択した pack の意味を理解する
2. 公開 facts と risk signal を確認する
3. try / install / compare / download の member action を選ぶ
4. 同じ pack context を保ったまま install sync 範囲を調整する

## 現在の Market Center Baseline

detail layer は、現在実装済みの `/market` baseline から派生しなければなりません。

baseline の要点:

1. public-first の market entry
2. compact で monochrome な technical-editorial header
3. header 下に置かれた大きな Spotlight 風 search
4. search 下の restrained な sort / result controls
5. filter rail + public card grid による browse surface
6. card click 後にだけ開く detail shell

detail layer は、この baseline の自然な次の深さとして見える必要があります。

## 必須 Data Contract

使い続ける contract:

1. `pack_id`
2. display title
3. `version`
4. `maintainer`
5. `pack_type`
6. `risk_level`
7. `compatibility`
8. `review_labels`
9. `warning_flags`
10. `sections`
11. summary / description
12. updated-at metadata
13. public source / audit facts

## DOM と Runtime 制約

壊してはいけない container:

1. `marketDetailArea`
2. `marketDetailControlStore`
3. `marketDetailActionCluster`
4. `marketDetailInstallSectionsShell`
5. `marketDetailInstallOptionsShell`
6. `marketSummary`

保持すべきこと:

1. desktop drawer / mobile sheet behavior
2. variant 切り替え中の pack context 保持
3. member action が発火する時だけ auth gate
4. standalone script loading と globalScope export 互換

## 派生ルール

強く継承する内容:

1. current market center の monochrome technical-editorial language
2. public facts first、actions second の hierarchy
3. page は browse、detail layer は act という semantics
4. 抑制されたトーン
5. current page に自然につながる action rail
6. ship する action control は主パネルへ統合し、下部に別の member-actions card を残さない

許容される変更:

1. detail layer 内部の再配置
2. trust / facts / actions の先頭順
3. evidence / metadata の grouping

許容されない変更:

1. market center の personality から逸脱すること
2. radically different な visual system を導入すること
3. 派生元 page より detail layer を主役に見せること
4. 古い Stitch market-hub 案を stylistic source として再利用すること

## Stitch 呼び出し基準

Stitch では `Design.md` の英語 prompt block を唯一の prompt source として使います。日本語説明は補助用です。

固定ルール:

1. Stitch の対象は clicked-card detail layer のみ
2. internal では Variant 1-5 を保持してよいが、ship する detail layer に visible な切替行は置かないこと
3. clear な member action rail を保つこと
4. public facts は login 前でも読めること
5. 認証は member action 開始時のみ要求すること
6. install 前に section-selective sync を明確に選べること
7. `memory_store`、`conversation_history`、`knowledge_base` は optional sync target として見えること
8. upload / submit UI は user panel 側に残し、detail layer へ持ち込まないこと

## 現在の Native 実装方針

現在の local implementation は `variant_3` を基準にしています。

1. `variant_3` が最優先の深化対象
2. 左に public facts、右に member-action readiness を置く
3. 実際の protected action は `Action readiness` ブロックへ統合し、viewport 下に別カードを残さない
4. install-time selective sync は native member-action flow の一部
5. `memory_store`、`conversation_history`、`knowledge_base` は install 時に deselect 可能
6. install-sync section を detail viewport 内で唯一の section 表示として扱い、別の declared sections ブロックを重ねない
7. install source / preflight / force-reinstall と local-installations state/list は install-sync と review-signal の間へ置く
8. upload / submit UI は detail layer へ戻さない
9. 今後 Stitch を再実行する前に `Design.md` を必ず更新する

## 受け入れチェック

1. variant 切り替えでも pack context が安定
2. member action rail が継続利用可能
3. 必須 public facts を落とさない
4. standalone WebUI runtime model を壊さない
5. current market-center baseline 由来であると視覚的に分かる
6. 古い market hub に戻る drift は reject

## 現在有効な結果

- 旧 session `14909211256281812924` と、その後の archive project `projects/614617403044256572` は履歴比較用のみで、current visual baseline としては使いません。
- 現在確認済みの baseline project: `projects/1791941634823407461`
- 現在確認済みの baseline screen: `3ef1d2a12c3449f593141520a70ec987`
- baseline title: `Sharelife Market Detail Concept`
- current 5-variant status:
  - variant session: `14727920063696137864`
  - `variant_1`: `0a22321fc4244a8cbb4b80c7ff88543a`
  - `variant_2`: `926623465dd94241a9f2f4ba68811dad`
  - `variant_3`: `4d71151e5e0a499fbbb9e2b78b7676aa`
  - `variant_4`: `2faed839bb5d4de4ad6887c795b30733`
  - `variant_5`: `9ad760cf710c4b83972b04fbe2e39580`
- current implementation preference:
  - `variant_3` を native 実装の主アンカーとして継続
  - `variant_5` は checklist-first 実行導線の補助参照として最も明快
  - `variant_2` は operator-console 密度の参照として残し、default 方向にはしない
