# プラグインエコシステム Round 2 基線（v0.3.13）

本ドキュメントは、`sharelife` を機能プラグイン段階からプラットフォーム段階へ進める基線設計です。

## 最小版（MVP）

1. `plugin.manifest.v2.json`（プラグイン契約）
2. `astr-agent.yaml`（Agent/Pipeline 契約）
3. Capability Gateway（権限宣言ベースの実行制御）
4. `create-astrbot-plugin`（スキャフォールド）
5. ホットリロード開発
6. リスクラベル・互換性チェック・導入確認・監査を備えたマーケット運用

## 実装状況（M1-M5）

1. `M1` 完了: スキーマ凍結 + サンプル + CI 検証（`scripts/validate_protocol_examples.py`）。
2. `M2` 完了: Capability Gateway（`sharelife/application/services_capability_gateway.py`）で未宣言高リスク能力を deny-by-default。
3. `M3` 完了: DX コマンド（`scripts/create-astrbot-plugin` / `scripts/sharelife-hot-reload`）と SDK 型契約（`sharelife/sdk/contracts.py`）。
4. `M4` 完了: Pipeline Orchestrator（`sharelife/application/services_pipeline.py`）で A->B 連鎖と `retry/skip/abort` を実装。
5. `M5` 完了: ガバナンスメタデータ（`capability_summary` / `compatibility_matrix` / `review_evidence`）と非公開 Featured ゲート。

M5 後の拡張:

1. `M6` 完了: profile-pack の plugin install 実行閉ループ（`plan -> confirm -> execute`）は実装済み。コマンド実行は既定で無効、接頭辞 allowlist + timeout、実行証跡の永続化、任意の `require_success_before_apply` で安全性と再現精度を両立。

## アーキテクチャ図（文字）

```text
Plugin Lifecycle -> Capability Gateway -> Runtime Adapters
        |                  |                    |
        v                  v                    v
     Event Bus <-> Pipeline Orchestrator <-> Risk/Audit Engine
        |                  |                    |
        +---------- WebUI/CLI + Registry + Package Storage
```

## コアコンポーネント

1. Lifecycle Manager
2. Capability Gateway
3. Manifest/Schema Validator
4. Pipeline Orchestrator
5. Risk/Audit Engine
6. Registry Service
7. DX Toolchain

## データフロー

1. 公開フロー：検証 -> パッケージ化 -> スキャン -> ラベル付け -> カタログ登録
2. 導入フロー：閲覧 -> 互換性確認 -> 権限確認 -> 導入 -> 監査記録
3. 実行フロー：トリガー -> 権限判定 -> プラグイン実行 -> 監査
4. Profile/Extension Pack：export -> import -> dry-run -> apply/rollback

## 技術スタック

1. Python 3.12 / FastAPI / Pydantic
2. 既存 Sharelife モジュール境界
3. WebUI / VitePress / GitHub Actions / GitHub Pages / GitHub Releases

## 構築順序

1. 契約スキーマ凍結
2. Capability Gateway 実装
3. DX（スキャフォールド + ホットリロード）実装
4. Composable Pipeline 実装
5. マーケット治理（可視化証拠・審査支援）強化

## エッジケース

1. 権限宣言不足
2. 互換性不一致
3. ホットリロード時の状態汚染
4. パイプライン中間失敗
5. 高リスク導入時の管理者確認不足

## 拡張戦略

1. 公式/コミュニティ/私有 Registry の統合
2. 段階的隔離（Capability -> Container/WASM）
3. メンテナ信用・プラグイン健全性スコア
4. SDK v4 互換ブリッジ

## 想定ボトルネック

1. DX 不足による開発者流入停滞
2. 権限 enforcement 不整合による信頼低下
3. 手動審査コスト肥大
4. 契約ドリフトによる組み合わせ劣化

## v2 最適化

1. 強隔離サンドボックス
2. プラグイン資源予算（CPU/メモリ/IO）
3. リスク/互換性ベース推薦
4. トレーシングと失敗分析
5. Astr UI Kit の統一
6. Web マーケットからローカル AstrBot へのワンクリック導入
