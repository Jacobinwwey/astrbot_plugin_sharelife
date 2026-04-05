# Sharelife クイックスタート

このチュートリアルでは、`sharelife` の最小ワークフローを確認します。

## 3分ファストパス

1. まず設定生成:

```bash
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
```

2. チャットで即時確認:

```text
/sharelife_pref
/sharelife_market
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

3. 動作確認後に本ページの完全手順へ進みます。  
一画面版は [3分クイックスタート](/ja/tutorials/3-minute-quickstart) を参照。

## 前提条件

1. Python 3.12
2. AstrBot 実行環境
3. `pip install -r requirements.txt` で依存関係をインストール済み

任意: `/sharelife_webui` でスタンドアロン WebUI の URL を確認できます。

## ステップ 1: 既定の設定を確認

```text
/sharelife_pref
```

既定値:

- `execution_mode=subagent_driven`
- `observe_task_details=off`

## ステップ 2: 実行モードを変更

```text
/sharelife_mode inline_execution
```

その後、`/sharelife_pref` で反映を確認します。

## ステップ 3: タスク詳細観測を有効化

```text
/sharelife_observe on
```

`/sharelife_pref` を再実行し、`observe_task_details=on` を確認します。

## ステップ 4: トライアル状態確認と管理者適用フロー

まず一般ユーザーで試用を開始します。

```text
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

2 つ目のコマンドでは `not_started`・`active`・`expired` の状態と TTL / 残り秒数を確認できます。

同一テンプレートで再試行すると管理者キューに入ります。

管理者コマンド:

```text
/sharelife_retry_list
/sharelife_retry_lock <request_id>
/sharelife_retry_decide <request_id> approve <request_version> <lock_version>
/sharelife_dryrun community/basic 1.0.0
/sharelife_apply <plan_id>
/sharelife_rollback <plan_id>
```

`plan_id` を省略すると `plan-community-basic` のような既定値が使われます。

## ステップ 5: コミュニティ投稿とインストール

ユーザー投稿:

```text
/sharelife_submit community/basic 1.0.0
```

管理者レビュー:

```text
/sharelife_submission_list
/sharelife_submission_decide <submission_id> approve
```

公開後の利用:

```text
/sharelife_market
/sharelife_install community/basic
/sharelife_prompt community/basic
/sharelife_package community/basic
/sharelife_audit 20
```
