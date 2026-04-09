# ユーザーパネル + マーケット再設計 実行計画

> 日付: `2026-04-04`  
> 担当: WebUI Architecture  
> 対象: member パネルと `/market` の機能等価化

## 0. 現在の実装状況

現行コードベースでは次を実装済み:

1. `/member` で 4 つのユーザーワークフローを第一級 UI として提供:
   - Spotlight 型ストア検索
   - インストール管理
   - ドラッグアンドドロップ対応アップロードセンター
   - タスクキューと履歴
2. `/market` に同等の install/upload コントロール、ローカルインストール更新、ドラッグアンドドロップ UI を追加。
3. `/market` に member 所有アップロード管理ビューを追加:
   - 自分の template submission 一覧 + detail ジャンプ
   - 自分の profile-pack submission 一覧 + detail ジャンプ
4. 後方互換な API 拡張を実装:
   - `GET /api/member/installations`
   - `POST /api/member/installations/refresh`
   - `GET /api/member/submissions`
   - `GET /api/member/submissions/detail`
   - `GET /api/member/profile-pack/submissions`
   - `GET /api/member/profile-pack/submissions/detail`
   - `install_options`
   - `upload_options`
   - `submit_options`
5. interface test、WebUI unit test、browser E2E に検証を追加。
6. `/member` は Spotlight 優先の構成に更新済みです。上部に言語切替・ローカル更新・単一検索入口を集約し、member 側結果面から重複した `Market Hub` 見出しを除去しました。

現在のトレードオフ:

1. `install_options.source_preference=generated` は実際に package 解決経路へ反映済み。
2. それ以外の option block は正規化・永続化・UI/API 返却までは実装済みだが、下流の governance 意味論まで全面適用はまだ完了していない。

次の収束項目:

1. `/member` の top-bar 主操作は汎用的な config import 表現ではなく、`Import Local AstrBot Config` 相当の明示文言へ変更する。
2. `/member` の top utility には member 安全な入口だけを残す:
   - `Member Console`
   - `Market Hub`
3. reviewer/admin/full console リンクと developer-mode toggle は CSS で隠すのではなく、member DOM から除去する。
4. 生の AstrBot import 成功後は、section 確認用の upload review modal を必ず開く。

## 1. 目標

既存契約と権限境界を維持したまま、ユーザー向け WebUI を次の 4 ワークフローに再編する。

1. Store Search  
2. Manage Installations  
3. Upload Center  
4. Download & Task Management

## 2. 変更不可の基準

1. 既存の Vanilla モジュール構成を維持（`app.js`、`market_page.js` など）。  
2. `/api/ui/capabilities` による capability ゲートを維持。  
3. `webui_i18n.js` のキー設計を維持。  
4. テスト/オーケストレーションが参照する DOM ID を維持。  

## 3. IA と UI の到達形

### 3.1 member 面

1. Top bar:
   - Spotlight 型グローバル検索
   - 言語切替
   - 常時表示 `Import Local AstrBot Config`
2. 主表示: インストール済み一覧。
3. 補助表示:
   - アップロード Drop zone + オプション
   - ダウンロード/タスクキュー（進捗 + 履歴）
4. モバイル:
   - サイドナビはドロワー化
   - 検索は単一行または積層でも主導線を維持

### 3.2 `/market` 等価化

`/market` はアップロード/インストールのオプション制御を member 面と同等で提供する。

## 4. API 契約拡張（後方互換）

### 4.1 member インストール API

1. `GET /api/member/installations`  
2. `POST /api/member/installations/refresh`
3. `GET /api/member/submissions`
4. `GET /api/member/submissions/detail`
5. `GET /api/member/profile-pack/submissions`
6. `GET /api/member/profile-pack/submissions/detail`

レスポンス envelope:
`{ ok, message, data, error? }`

### 4.2 payload 拡張

1. `POST /api/templates/install`
   - `install_options.preflight: bool`
   - `install_options.force_reinstall: bool`
   - `install_options.source_preference: auto|uploaded_submission|generated`
2. `POST /api/templates/submit`
   - `upload_options.scan_mode: strict|balanced`
   - `upload_options.visibility: community|private`
   - `upload_options.replace_existing: bool`
3. `POST /api/profile-pack/submit`
   - `submit_options.pack_type`
   - `submit_options.selected_sections`
   - `submit_options.redaction_mode`

## 5. Stitch 連携ルール

1. `DESIGN.md` を単一の設計真実源にする。  
2. member / market レイアウトを Stitch で生成。  
3. 生成片はアダプタ境界でのみ反映:
   - runtime ID 保持
   - i18n key 保持
   - capability バインディング保持
4. イベント配線や RBAC 境界を壊す片はマージしない。

## 6. 検証マトリクス

1. Interface テスト:
   - member installation API
   - 拡張 payload の検証/既定値
2. WebUI ユニット:
   - installation/task/options の ViewModel マッピング
   - i18n key 完全性
3. E2E:
   - card click -> detail
   - options 付き upload/install
   - local refresh による installation 反映
   - member/market 等価性

## 7. リスクと制御

1. リスク: 生成マークアップで既存バインディング破壊  
   制御: ID 保持チェックを必須化。
2. リスク: UX 簡素化でパワーユーザー操作を損失  
   制御: 高度操作は削除ではなく折りたたみ。
3. リスク: UI と backend の capability ドリフト  
   制御: 新 UI 操作は `CONTROL_CAPABILITY_MAP` 反映後に公開。
4. リスク: member DOM に特権 console 導線が残り続ける  
   制御: `member.html` から特権リンク/トグルを除去し、権限制御は server 側でも継続する。
