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

## ステップ 4: トライアル状態確認とローカル install への引き渡し

まず一般ユーザーで試用を開始します。

```text
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

2 つ目のコマンドでは `not_started`・`active`・`expired` の状態と TTL / 残り秒数を確認できます。

その後はローカル member install フローへ進みます:

```text
/sharelife_market
/sharelife_prompt community/basic
/sharelife_package community/basic
```

実際の install 操作はローカル WebUI の `/member` または `/market` で行います。利用できる install オプション:

- `preflight`
- `force_reinstall`
- `source_preference=auto|uploaded_submission|generated`

## ステップ 5: upload とコミュニティ投稿

template upload フロー:

1. ローカル WebUI の `/member` または `/market` を開きます。
2. template package を選択するか、生成済み package 出力を使います。
3. 直接アップロード上限は `20 MiB` です。
4. upload オプション:
   - `scan_mode=strict|balanced`
   - `visibility=community|private`
   - `replace_existing=true|false`
5. 投稿後は `My Submissions` で結果を確認します。

profile-pack 投稿フロー:

1. ローカル artifact を準備し、`artifact_id` を控えます。
2. `/member` または `/market` から投稿します。
3. submit オプション:
   - `pack_type`
   - `selected_sections`
   - `redaction_mode`
   - `replace_existing`
4. `My Profile-Pack Submissions` で owner スコープの状態と export を確認します。
