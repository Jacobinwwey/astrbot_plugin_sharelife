# 3分クイックスタート

このページは member 側の最短経路だけを扱います。まず 3 分で動かし、詳細は後で確認します。

## 0. 人間向けクイック導入（最小）

```bash
pip install -r requirements.txt
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
pytest -q && node --test tests/webui/*.js
```

対話式で生成する場合:

```bash
bash scripts/sharelife-init-wizard --output config.generated.yaml
```

## 1. AI 向けワンコピー導入 Prompt

```text
あなたはターミナル設定エージェントです。作業ディレクトリは `astrbot_plugin_sharelife`。次を順に実行: (1) `pip install -r requirements.txt`; (2) `bash scripts/sharelife-init-wizard --yes --output config.generated.yaml`; (3) `pytest -q`; (4) `node --test tests/webui/*.js`。失敗したら即停止し、「失敗ステップ + 根因 + 修正コマンド」だけ出力。全部成功したら `READY`、生成した設定ファイルパス、検証コマンド4つ（`/sharelife_pref` `/sharelife_market` `/sharelife_trial community/basic` `/sharelife_trial_status community/basic`）だけ出力。
```

## 2. チャットで動作確認

```text
/sharelife_pref
/sharelife_market
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

期待値: trial 状態が明示され、market 応答が返ること。

## 3. Member 側への引き渡し確認

1. `/sharelife_webui` でローカル WebUI を開きます。
2. 保護された member 操作は `/member` または `/market` で続行します。
3. install、upload、profile-pack 投稿はローカル UI で完結します。
4. 特権 moderation や復旧手順は公開 docs に含めません。

## 4. 次の導線

1. 詳細版は [クイックスタート](/ja/tutorials/get-started)。
2. 設定運用は [初期化ウィザードと設定テンプレート](/ja/how-to/init-wizard-and-config-template)。
3. リポジトリ直下の [QUICKSTART.md](https://github.com/Jacobinwwey/astrbot_plugin_sharelife/blob/main/QUICKSTART.md) も参照してください。
