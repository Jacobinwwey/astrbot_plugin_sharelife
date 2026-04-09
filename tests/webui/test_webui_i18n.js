const test = require("node:test")
const assert = require("node:assert/strict")

const {
  DEFAULT_LOCALE,
  SUPPORTED_LOCALES,
  normalizeLocale,
  getMessage,
  applyLocale,
} = require("../../sharelife/webui/webui_i18n.js")

test("normalizeLocale resolves supported locale and fallback", () => {
  assert.equal(DEFAULT_LOCALE, "en-US")
  assert.ok(SUPPORTED_LOCALES.includes("zh-CN"))
  assert.ok(SUPPORTED_LOCALES.includes("ja-JP"))
  assert.equal(normalizeLocale("zh-cn"), "zh-CN")
  assert.equal(normalizeLocale("ja-jp"), "ja-JP")
  assert.equal(normalizeLocale("fr-FR"), "en-US")
})

test("getMessage returns locale-specific translation with fallback", () => {
  assert.equal(
    getMessage("zh-CN", "profile_pack.market.submit_btn", "Submit To Community"),
    "投稿到社区",
  )
  assert.equal(
    getMessage("ja-JP", "profile_pack.market.submit_btn", "Submit To Community"),
    "コミュニティへ投稿",
  )
  assert.equal(
    getMessage("en-US", "profile_pack.market.submit_btn", "Submit To Community"),
    "Submit To Community",
  )
  assert.equal(
    getMessage("en-US", "missing.key", "Fallback Text"),
    "Fallback Text",
  )
  assert.equal(
    getMessage("zh-CN", "templates.idle", ""),
    "加载模板列表以浏览已发布包。",
  )
  assert.equal(
    getMessage("ja-JP", "submissions.idle", ""),
    "保留中コミュニティ package を確認するには submission 一覧を読み込んでください。",
  )
  assert.equal(
    getMessage("zh-CN", "panel.compare.empty", ""),
    "选择投稿行以加载对比结果。",
  )
  assert.equal(
    getMessage("ja-JP", "workspace.submission_route_idle", ""),
    "Submission workspace は idle です。submission 行を選択するか、Load Submission Detail を使ってください。",
  )
  assert.equal(
    getMessage("zh-CN", "moderation.summary_idle", ""),
    "选择投稿行以回填审核字段并加载对比状态。",
  )
  assert.equal(
    getMessage("zh-CN", "detail.label.prompt_length", ""),
    "提示词长度",
  )
  assert.equal(
    getMessage("zh-CN", "risk_glossary.item.high.title", ""),
    "高风险",
  )
  assert.equal(
    getMessage("ja-JP", "risk_glossary.group.warning_flags", ""),
    "警告フラグ",
  )
  assert.equal(
    getMessage("ja-JP", "risk_glossary.item.prompt_injection_detected.title", ""),
    "Prompt injection 検出",
  )
  assert.equal(
    getMessage("ja-JP", "panel.moderation.heading", ""),
    "Moderation",
  )
  assert.equal(
    getMessage("zh-CN", "button.login", ""),
    "登录",
  )
  assert.equal(
    getMessage("ja-JP", "button.profile_import_dryrun", ""),
    "Import + Dry-Run",
  )
  assert.equal(
    getMessage("zh-CN", "market.auth.line", ""),
    "鉴权：{status}",
  )
  assert.equal(
    getMessage("en-US", "button.developer_mode_off", ""),
    "Developer Mode: OFF",
  )
  assert.equal(
    getMessage("en-US", "enum.status.replaced", ""),
    "replaced",
  )
  assert.equal(
    getMessage("en-US", "enum.status.running", ""),
    "running",
  )
  assert.equal(
    getMessage("en-US", "enum.status.stale", ""),
    "stale",
  )
  assert.equal(
    getMessage("zh-CN", "enum.status.replaced", ""),
    "已替换",
  )
  assert.equal(
    getMessage("zh-CN", "enum.status.running", ""),
    "执行中",
  )
  assert.equal(
    getMessage("zh-CN", "enum.status.stale", ""),
    "已过旧",
  )
  assert.equal(
    getMessage("ja-JP", "enum.status.replaced", ""),
    "差し替え済み",
  )
  assert.equal(
    getMessage("ja-JP", "enum.status.running", ""),
    "実行中",
  )
  assert.equal(
    getMessage("ja-JP", "enum.status.stale", ""),
    "期限切れ",
  )
  assert.equal(
    getMessage("zh-CN", "developer_mode.status.on", ""),
    "开发者模式：已开启",
  )
  assert.equal(
    getMessage("ja-JP", "scan.evidence.header", ""),
    "リスク位置情報 ({count})",
  )
  assert.equal(
    getMessage("en-US", "scan.evidence.jump_hint", ""),
    "Developer mode: click an evidence row to open compare view.",
  )
  assert.equal(
    getMessage("en-US", "audit.output.summary.header", ""),
    "Audit Summary",
  )
  assert.equal(
    getMessage("zh-CN", "audit.output.summary.actions", ""),
    "高频动作",
  )
  assert.equal(
    getMessage("ja-JP", "audit.output.events.header", ""),
    "最新イベント ({count})",
  )
  assert.equal(
    getMessage("zh-CN", "compare.evidence_focus", ""),
    "证据 {rule} @ {file}:{line}:{column}",
  )
  assert.equal(
    getMessage("zh-CN", "profile_pack.compatibility.heading", ""),
    "兼容性指引",
  )
  assert.equal(
    getMessage("en-US", "profile_pack.section.memory_store.title", ""),
    "Memory Store (Stateful)",
  )
  assert.equal(
    getMessage("ja-JP", "profile_pack.issue.section_hash_mismatch_with_section", ""),
    "Section hash mismatch: {section}",
  )
  assert.equal(
    getMessage("zh-CN", "profile_pack.review.field.plugin_install_failure_groups", ""),
    "插件安装失败分组",
  )
  assert.equal(
    getMessage("en-US", "profile_pack.review.group.policy_blocked", ""),
    "policy",
  )
  assert.equal(
    getMessage("zh-CN", "profile_pack.action.shortcut.opened_plugin_install", ""),
    "已定位到插件安装控制区，便于继续处理。",
  )
  assert.equal(
    getMessage("ja-JP", "profile_pack.action.shortcut.developer_mode_required", ""),
    "この詳細を確認するには Developer Mode を先に有効化してください。",
  )
  assert.equal(
    getMessage("zh-CN", "profile_pack.action.shortcut.developer_mode_required_pending", ""),
    "请先开启开发者模式，动作会在开启后自动继续。",
  )
  assert.equal(
    getMessage("en-US", "profile_pack.action.shortcut.prefill_applied", ""),
    "Prefill applied: {details}",
  )
  assert.equal(
    getMessage("zh-CN", "profile_pack.action.shortcut.prefill_sections", ""),
    "sections={sections}",
  )
  assert.equal(
    getMessage("ja-JP", "profile_pack.action.shortcut.prefill_plugin_ids", ""),
    "plugin_ids={plugin_ids}",
  )
  assert.equal(
    getMessage("en-US", "market.entry.subtitle_public", ""),
    "Public discovery first. Compare facts, then cross into protected member actions.",
  )
  assert.equal(
    getMessage("en-US", "market.sidebar.category.all", ""),
    "All Catalog",
  )
  assert.equal(
    getMessage("zh-CN", "market.sidebar.category.low_risk", ""),
    "低风险优先",
  )
  assert.equal(
    getMessage("ja-JP", "market.catalog.stage_heading", ""),
    "公開カタログ",
  )
  assert.equal(
    getMessage("en-US", "member.upload_detail.preview_heading", ""),
    "Selected Content",
  )
  assert.equal(
    getMessage("zh-CN", "member.upload_detail.preview_empty", ""),
    "当前节点没有可展示的预览内容。",
  )
  assert.equal(
    getMessage("ja-JP", "member.upload_detail.preview_truncated", ""),
    "プレビューは途中で切り詰められています。",
  )
  assert.equal(
    getMessage("zh-CN", "market.search.spotlight_hint", ""),
    "先搜索 pack、标签、维护者与风险信号，再决定是否打开 detail。",
  )
  assert.equal(
    getMessage("ja-JP", "market.detail.member_actions", ""),
    "メンバー操作",
  )
  assert.equal(
    getMessage("en-US", "market.entry.default_detail_open", ""),
    "Open default detail",
  )
  assert.equal(
    getMessage("zh-CN", "market.entry.stat_variant_value", ""),
    "V3 / 5 个方案",
  )
  assert.equal(
    getMessage("ja-JP", "market.search.capability_selective_sync", ""),
    "install 時に選択同期",
  )
  assert.equal(
    getMessage("en-US", "button.import_astrbot_config", ""),
    "Import Local AstrBot Config",
  )
  assert.equal(
    getMessage("zh-CN", "button.import_astrbot_config", ""),
    "导入本机 AstrBot 配置",
  )
  assert.equal(
    getMessage("ja-JP", "button.import_astrbot_config", ""),
    "ローカル AstrBot 設定を取り込む",
  )
  assert.equal(
    getMessage("zh-CN", "button.review_imported_configs", ""),
    "审阅已导入配置包",
  )
  assert.equal(
    getMessage("en-US", "button.withdraw_submission", ""),
    "Withdraw Submission",
  )
  assert.equal(
    getMessage("zh-CN", "member.imports.heading", ""),
    "已导入配置包",
  )
  assert.equal(
    getMessage("zh-CN", "member.imports.format_notice", ""),
    "支持 Sharelife 标准 zip、AstrBot 备份 zip、cmd_config.json 与 abconf_*.json；原始 AstrBot 输入会先转换为降级草稿。",
  )
  assert.equal(
    getMessage("ja-JP", "member.imports.idle", ""),
    "まだ取り込まれた設定パックはありません。",
  )
  assert.equal(
    getMessage("en-US", "member.upload_detail.title", ""),
    "Upload Details",
  )
  assert.equal(
    getMessage("en-US", "member.upload_detail.import_source_astrbot_raw", ""),
    "Raw AstrBot export (converted)",
  )
  assert.equal(
    getMessage("en-US", "member.upload_detail.inspector_title", ""),
    "Section Inspector",
  )
  assert.equal(
    getMessage("zh-CN", "member.upload_detail.inspector_empty", ""),
    "从左侧选择一个 section 或条目后，可在这里查看并继续细化上传范围。",
  )
  assert.equal(
    getMessage("ja-JP", "member.upload_detail.children_heading", ""),
    "選択可能な子項目",
  )
  assert.equal(
    getMessage("zh-CN", "detail.label.compatibility_notes", ""),
    "兼容性提示",
  )
  assert.equal(
    getMessage("en-US", "profile_pack.issue.astrbot_raw_import_converted", ""),
    "Converted from a raw AstrBot export. Review every section before submission or apply.",
  )
  assert.equal(
    getMessage("en-US", "profile_pack.issue.astrbot_backup_runtime_payload_omitted", ""),
    "Full AstrBot backup runtime payloads were omitted during conversion.",
  )
  assert.equal(
    getMessage("en-US", "profile_pack.issue.astrbot_operator_fields_omitted", ""),
    "AstrBot operator-only fields were omitted during conversion.",
  )
  assert.equal(
    getMessage("en-US", "profile_pack.issue.astrbot_plugin_wildcard_unresolved", ""),
    "AstrBot plugin wildcard '*' could not be resolved to a concrete plugin list.",
  )
  assert.equal(
    getMessage("en-US", "enum.status.withdrawn", ""),
    "withdrawn",
  )
  assert.equal(
    getMessage("en-US", "market.install.sections.heading", ""),
    "Install Sections",
  )
  assert.equal(
    getMessage("zh-CN", "market.install.sections.none_selected", ""),
    "当前未选择任何 section，安装时将跳过 section 同步。",
  )
  assert.equal(
    getMessage("ja-JP", "market.install.sections.summary_stateful", ""),
    "{selected}/{total} sections selected · {stateful} stateful/local sections can be skipped",
  )
  assert.equal(
    getMessage("en-US", "market.variant.tab_1", ""),
    "Variant 1",
  )
})

test("applyLocale updates text nodes, placeholder nodes and html lang", () => {
  const attrs = {}
  const textNode = {
    textContent: "Submit To Community",
    getAttribute(name) {
      if (name === "data-i18n-key") return "profile_pack.market.submit_btn"
      return null
    },
  }
  const placeholderNode = {
    placeholder: "artifact_id for community submit",
    getAttribute(name) {
      if (name === "data-i18n-placeholder-key") return "profile_pack.market.submit_placeholder"
      return null
    },
  }
  const root = {
    querySelectorAll(selector) {
      if (selector === "[data-i18n-key]") return [textNode]
      if (selector === "[data-i18n-placeholder-key]") return [placeholderNode]
      return []
    },
    documentElement: {
      setAttribute(name, value) {
        attrs[name] = value
      },
    },
  }

  const zhLocale = applyLocale(root, "zh-CN")
  assert.equal(zhLocale, "zh-CN")
  assert.equal(textNode.textContent, "投稿到社区")
  assert.equal(placeholderNode.placeholder, "用于社区投稿的 artifact_id")
  assert.equal(attrs.lang, "zh-CN")

  const fallbackLocale = applyLocale(root, "fr-FR")
  assert.equal(fallbackLocale, "en-US")
  assert.equal(textNode.textContent, "Submit To Community")
  assert.equal(placeholderNode.placeholder, "artifact_id for community submit")
  assert.equal(attrs.lang, "en-US")
})
