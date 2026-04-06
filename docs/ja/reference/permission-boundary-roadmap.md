# 権限制御境界とロール分離ロードマップ（User / Reviewer / Admin / Developer）

> 基準バージョン：`v1.0`  
> 最終固定日：`2026-04-06`  
> 対象：Sharelife WebUI、API、コマンド面、および公開 VitePress ドキュメント

## 1. 目的と原則

このロードマップは、ロール分離の方向を維持しつつ、不要な認証複雑性を抑え、公開露出面をさらに整理するための基準です。

基本原則：
- 機能追加より先にロール境界を定義する。
- ユーザー向け公開面は最小権限で設計する。
- 公開ドキュメントは運用 runbook ではない。安定した境界と挙動だけを公開し、機微な認証・復旧手順は私有文書に残す。
- 認可セマンティクスは固定する。未認証は `401`、認証済みだが権限不足は `403` を返す。

## 2. 実行時ロールマトリクス

| ロール | 許可 | 禁止 |
| --- | --- | --- |
| User | マーケット検索、インストール/削除、アップロード/ダウンロード、進捗確認、自分の保留中リソースに対する owner-aware 操作 | 審査決裁、strict apply、rollback、reviewer/admin キー管理 |
| Reviewer | 審査キュー処理、リスクラベル付与、審査決裁、証跡確認 | システム級 apply/rollback、グローバル設定変更 |
| Admin | 公開運用、破壊的操作、reviewer 准入分配、reviewer 端末/セッションのリセット | 監査ログ改変 |
| Developer | 設計進化、API 拡張、テスト/文書保守 | 実行時認可バイパス |

補足：
- Sharelife は独立した実行時 `Creator` ロールを導入しません。リソース属主は認可ルールとして扱い、ログインロールにはしません。
- ローカル reviewer 端末ベース認証は過渡的な fallback 実装として維持します。発行・復旧・失効の具体 SOP は公開文書では扱いません。

## 3. 現在の進捗と未完了項目

### 3.1 完了済み
- member / reviewer / admin / market の独立ページとロール別導線。
- 特権ルートに対する route-level auth middleware と安定した `401` / `403` 動作。
- reviewer 招待、端末、セッションのバックエンド基礎実装。
- reviewer/device/action 集計監査。
- 公開 docs と私有 docs の分離。operator/auth レベルの runbook は公開サイトから外した。

### 3.2 まだ閉じていないもの
- `admin -> reviewer` キー管理は frontend から backend までまだ閉ループになっていません。
  - backend には invite/device/session の土台がある。
  - admin WebUI には reviewer ライフサイクル管理コンソールがまだ不足している。
- owner-aware 判定は全書き込み経路をまだ覆っていません。
  - 投稿や profile-pack リソースには owner 情報がある。
  - ただし、全ユーザー向け mutation に統一強制されてはいない。
- reviewer セッションモデルは今後の整理対象です。
  - ロードマップ上で reviewer 全体の single active session は目標状態としません。
  - 今後は device 単位の無効化へ寄せます。

## 4. 公開向け実行方針

### 4.1 認証方針
- まず既存のローカル auth モデルを一貫した状態に収束させる。
- reviewer 招待/端末モデルは fallback 実装として扱い、長期的な中心設計にはしない。
- 外部 identity provider（`OIDC` / `OAuth2` / 企業 IdP）は次段階の方向であり、今回の即時全面移行対象ではない。

### 4.2 Reviewer ワークスペース
- reviewer は技術証跡へアクセスできなければならない。
- 望ましい UX は「リスク要約を先に、技術 payload は展開で確認」です。
- 公開文書では “evidence-first review” を説明し、内部 payload 構造や詳細 runbook は公開しません。

### 4.3 ドキュメント契約
- 公開 docs は required role と deny behavior を明記する。
- 私有 docs は reviewer invite、device key、secret rotation、復旧、operator 手順を担う。
- 長期的には「コード側で権限宣言し、文書はそこから同期・生成する」方向へ移行する。

## 5. 受け入れ基準

以下を満たした時だけ、この段階を完了とする：
1. reviewer 招待/端末/セッション経路を含む API / WebUI テストが通る。  
2. 未認証で特権ルートに入ると `401`、認証済みだが越権なら `403` を返す。  
3. ユーザーの書き込み操作が owner-aware となり、他人の非公開リソースを操作できない。  
4. 公開 docs が reviewer/admin の運用手順、secret 処理、復旧手順を露出しない。  
5. `admin -> reviewer` キー管理閉ループが「進行中の作業」として明記され、完了済みとは扱われない。  

## 6. 次段階の重点

1. `admin -> reviewer` ライフサイクルを閉じる：
   - invite 発行
   - device 可視化とリセット
   - session revoke
   - audit trace
2. `Creator` ロールを増やさず、owner-aware backend enforcement を追加する。
3. reviewer セッション無効化を device 単位に整理する。
4. コード優先の権限宣言と docs 同期へ寄せる。
5. ローカルモデルが安定した後にのみ、外部 IdP 連携を評価する。  
