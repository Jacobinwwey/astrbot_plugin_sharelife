# 開発の進行中ワークストリーム（公開）

> 最終更新: `2026-04-11`  
> 対象: 現在進行中の公開向け実装トラック

## ストリーム A: member upload フロー収束

状態: `in progress`

完了:

1. upload detail モーダルと market detail UX の整合。
2. ローカル AstrBot import 後の section 深層内容選択の可視化（より深いネストノード対応）。
3. draft 単位の upload detail レビュー状態記憶（modal 再オープン + 同一セッション再読込で復元）。
4. ローカル AstrBot 再走査時の重複折りたたみを「最新 draft 優先」の決定的ルールへ変更し、import ストレージの反復順が揺れても古い draft が前面化しないようにした。

継続:

1. import / submit / revoke の長時間ループに対する E2E 安定化を継続。

公開受け入れ条件:

1. member が import -> review -> submit -> revoke を安定実行できる。
2. upload detail で細粒度 section 選択と反映確認が可能で、同一ブラウザセッションでの復元が決定的である。

## ストリーム B: AstrBot 相互運用の堅牢化

状態: `in progress`

完了:

1. import 診断に決定的な issue-group bucket（`integrity` / `security` / `version` / `conversion` / `environment` / `unknown`）を追加し、import payload と review evidence の双方で一貫して参照できるようにした。

継続:

1. 生 AstrBot export と profile-pack 正規化モデルのマッピングを継続改善。
2. 非互換/降格フィールドの「フィールド単位」診断説明を強化。

公開受け入れ条件:

1. import 結果が決定的な `compatibility_issues` を返す。
2. サポート対象 section でサイレント欠落が発生しない。

## ストリーム C: docs と公開面ガバナンス

状態: `in progress`

1. 公開 docs は interface 契約のみ、運用手順は private docs に分離維持。
2. 新規 docs は三言語の構造同等性を維持。

公開受け入れ条件:

1. i18n 構造検証と docs build が継続成功。
2. public 向けコミットで promotion gate が PASS。

## ストリーム D: CI / E2E 安定化

状態: `in progress`

1. WebUI E2E の揺らぎ箇所を継続的に分解・是正。
2. 環境間で fixture 決定性を維持。

公開受け入れ条件:

1. main の `ci` が連続 push で安定成功。
2. E2E 失敗に根因ラベルと対策状態が付与される。
