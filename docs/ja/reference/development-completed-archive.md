# 開発完了アーカイブ（公開）

> 最終更新: `2026-04-11`  
> 対象: コード/テスト/公開 docs で検証可能な完了事項

## 完了した主なストリーム

1. 権限制御境界の基線
- member/reviewer/admin/market をページとルートで分離し、認可セマンティクスを `401` / `403` で固定。
- member テンプレートから特権 UI を除去し、CSS 隠蔽依存を排除。

2. 公開同期の安全ゲート
- promotion gate が private docs ルート、secret 類ローカルファイル、gitlink/submodule モード変更、allowlist 外追加パスを遮断。
- private->public 同期は projection manifest とテストで拘束。

3. market/member capability ガード収束
- market 側 capability runtime が共有 helper を再利用し、ページ間の認可ドリフトを抑制。
- 匿名 member allowlist を API/WebUI の契約テストで検証。

4. 実行/インストールの永続契約
- upload/install/submit のオプション契約を正規化。
- submit 経路で冪等競合拒否（`idempotency_key_conflict`）を適用。

5. 分解ガバナンス
- 主要モノリスに CI 行数予算を導入し、再肥大化を抑止。

## 検証ソース

1. `tests/infrastructure/test_public_promotion_gate.py`
2. `tests/meta/test_market_capability_runtime_surface.py`
3. `tests/meta/test_decomposition_budget_surface.py`
4. `tests/interfaces/test_webui_server.py`
5. `tests/meta/test_permission_boundary_roadmap_surface.py`

## 境界メモ

本ページは公開契約のみ。  
運用 SOP、secret ローテーション、特権復旧手順は非公開 docs で管理。

