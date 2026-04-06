# 初期化ウィザードと設定テンプレート

このページは、設定ガイドを実行可能な導線へ置き換えるための運用ガイドです。

## 目的

1. 初回セットアップ失敗を減らす
2. Time-to-Value を短縮する
3. 設定説明をファイル内へ内蔵する（Self-Documenting Config）

## 対話式 Init Wizard

実行:

```bash
bash scripts/sharelife-init-wizard --output config.generated.yaml
```

非対話デフォルト:

```bash
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
```

主要オプション:

1. `--provider openai|claude|deepseek`
2. `--api-key <value>`
3. `--preset standard_qa|sharelife_companion|research_safe`
4. `--webui-auth true|false`
5. `--allow-anonymous-member true|false`
6. `--anonymous-member-user-id <value>`
7. `--anonymous-member-allowlist "POST /api/trial,GET /api/trial/status,..."`
8. `--enable-plugin-install-exec true|false`
9. `--print-only`

## Self-Documenting Config Template

利用ファイル:

```text
config.template.yaml
```

テンプレートに含まれる項目:

1. provider/model 設定
2. sharelife WebUI 認証とレート制御
3. profile-pack 署名/暗号化設定
4. plugin install 実行ゲート（既定無効、prefix allowlist、timeout）
5. 匿名 member モード既定値とエンドポイント allowlist 上書き設定

## 推奨運用

1. `config.template.yaml` は git 管理
2. wizard で `config.generated.yaml` をローカル生成
3. 実 secrets はローカル限定で管理
4. 設定変更後は `/sharelife_pref` と `/sharelife_trial_status` で即時確認
