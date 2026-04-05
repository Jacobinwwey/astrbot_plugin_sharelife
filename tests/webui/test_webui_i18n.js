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
