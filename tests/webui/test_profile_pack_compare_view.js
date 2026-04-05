const test = require("node:test")
const assert = require("node:assert/strict")

const {
  buildProfilePackCompareView,
  summarizePluginInstallExecution,
} = require("../../sharelife/webui/profile_pack_compare_view.js")

test("buildProfilePackCompareView returns empty state without compare payload", () => {
  const view = buildProfilePackCompareView({})

  assert.equal(view.empty, true)
  assert.match(view.summary, /No compare payload loaded/i)
  assert.deepEqual(view.cards, [])
  assert.deepEqual(view.sections, [])
})

test("summarizePluginInstallExecution groups attempt failures by reason class", () => {
  const summary = summarizePluginInstallExecution({
    status: "partial_failed",
    result: {
      installed_count: 1,
      failed_count: 2,
      blocked_count: 1,
      attempts: [
        { plugin_id: "a", status: "installed", reason: "completed" },
        { plugin_id: "b", status: "blocked", reason: "install_command_prefix_not_allowed" },
        { plugin_id: "c", status: "failed", reason: "command_failed" },
        { plugin_id: "d", status: "failed", timed_out: true, reason: "command_failed" },
      ],
    },
  })
  assert.equal(summary.status, "partial_failed")
  assert.equal(summary.installed_count, 1)
  assert.equal(summary.failed_count, 2)
  assert.equal(summary.blocked_count, 1)
  assert.deepEqual(summary.groups.policy_blocked, ["b"])
  assert.deepEqual(summary.groups.command_failed, ["c"])
  assert.deepEqual(summary.groups.timed_out, ["d"])
  assert.deepEqual(summary.groups.other, ["a"])
})

test("buildProfilePackCompareView maps compare payload to cards sections and warnings", () => {
  const view = buildProfilePackCompareView({
    status: "compare_ready",
    pack_id: "profile/community-runtime-compare",
    version: "1.0.0",
    selected_sections: ["plugins", "providers"],
    changed_sections: ["plugins"],
    changed_sections_count: 1,
    compatibility: "degraded",
    compatibility_issues: ["ASTRBOT_VERSION_MISMATCH"],
    scan_summary: {
      risk_level: "high",
      warning_flags: ["reveal_system_prompt"],
      prompt_injection: {
        detected: true,
        matched_rules: ["ignore_previous_instructions"],
      },
    },
    plugin_install: {
      status: "confirmation_required",
      confirmation_required: true,
      missing_plugins: ["community_tools"],
      latest_execution: {
        status: "partial_failed",
        result: {
          installed_count: 1,
          failed_count: 2,
          blocked_count: 1,
          attempts: [
            { plugin_id: "community_tools", status: "installed", reason: "completed" },
            { plugin_id: "tools_policy", status: "blocked", reason: "install_command_prefix_not_allowed" },
            { plugin_id: "tools_fail", status: "failed", reason: "command_failed" },
            { plugin_id: "tools_timeout", status: "failed", timed_out: true, reason: "command_failed" },
          ],
        },
      },
    },
    diff: {
      sections: [
        {
          section: "plugins",
          changed: true,
          before_hash: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          after_hash: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          before_size: 120,
          after_size: 260,
          changed_paths_preview: ["plugins.community_tools.enabled", "plugins.community_tools.version"],
          changed_paths_count: 2,
          changed_paths_truncated: false,
        },
        {
          section: "providers",
          changed: false,
          before_hash: "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          after_hash: "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          before_size: 480,
          after_size: 480,
        },
      ],
    },
  })

  assert.equal(view.empty, false)
  assert.match(view.summary, /1\/2 sections changed/i)

  const changedCard = view.cards.find((item) => item.label === "Changed Sections")
  assert.equal(changedCard.value, "1")
  assert.equal(changedCard.tone, "danger")

  const compatibilityCard = view.cards.find((item) => item.label === "Compatibility")
  assert.equal(compatibilityCard.value, "degraded")
  assert.equal(compatibilityCard.tone, "warning")

  const pluginCard = view.cards.find((item) => item.label === "Plugin Install")
  assert.equal(pluginCard.value, "confirmation required")
  assert.equal(pluginCard.tone, "danger")

  const pluginExecCard = view.cards.find((item) => item.label === "Plugin Install Exec")
  assert.equal(pluginExecCard.value, "partial failed")
  assert.equal(pluginExecCard.tone, "neutral")

  assert.deepEqual(
    view.highlights.map((item) => item.label),
    [
      "changed: plugins",
      "compatibility: degraded",
      "plugin install: confirmation required",
      "plugin install execution: partial failed",
    ],
  )

  const pluginsRow = view.sections.find((item) => item.section === "plugins")
  assert.ok(pluginsRow)
  assert.equal(pluginsRow.changed, true)
  assert.equal(pluginsRow.before_hash_short, "aaaaaaaaaaaa...")
  assert.equal(pluginsRow.after_hash_short, "bbbbbbbbbbbb...")
  assert.equal(pluginsRow.delta_size, 140)
  assert.equal(pluginsRow.change_overview, "plugins.community_tools.enabled, plugins.community_tools.version")
  assert.equal(pluginsRow.file_path, "sections/plugins.json")

  const providersRow = view.sections.find((item) => item.section === "providers")
  assert.ok(providersRow)
  assert.equal(providersRow.changed, false)
  assert.equal(providersRow.delta_size, 0)

  assert.deepEqual(
    view.warnings.map((item) => item.message),
    [
      "Compatibility: degraded (astrbot version mismatch)",
      "Plugin install confirmation required: community_tools",
      "Plugin install execution: partial failed (installed=1, failed=2, blocked=1)",
      "Plugin install policy blocks: tools_policy",
      "Plugin install command failures: tools_fail",
      "Plugin install timeouts: tools_timeout",
      "Scan risk level: high",
      "Warning flags: reveal system prompt",
      "Prompt injection detected: ignore previous instructions",
    ],
  )
})

test("buildProfilePackCompareView supports localized labels when i18n helpers are provided", () => {
  const messages = {
    "profile_pack.compare.card.pack": "配置包",
    "profile_pack.compare.summary": "配置包 {pack_id}：{changed}/{selected} 已变化",
    "profile_pack.compare.highlight.changed": "已变化：{section}",
    "market.compare.change_paths_summary_exact": "{paths}",
    "market.compare.no_changes": "无变化",
  }
  const t = (key, fallback = "") => (Object.hasOwn(messages, key) ? messages[key] : fallback)
  const f = (key, fallback = "", tokens = {}) =>
    String(t(key, fallback)).replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, token) => String(tokens[token] ?? ""))

  const view = buildProfilePackCompareView(
    {
      status: "compare_ready",
      pack_id: "profile/localized",
      selected_sections: ["plugins"],
      changed_sections: ["plugins"],
      changed_sections_count: 1,
      diff: {
        sections: [
          {
            section: "plugins",
            changed: true,
            before_hash: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            after_hash: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            before_size: 10,
            after_size: 20,
            changed_paths_preview: ["plugins.community.enabled"],
            changed_paths_count: 1,
            changed_paths_truncated: false,
          },
        ],
      },
    },
    { t, f },
  )

  assert.equal(view.cards[0].label, "配置包")
  assert.equal(view.summary, "配置包 profile/localized：1/1 已变化")
  assert.equal(view.highlights[0].label, "已变化：plugins")
  assert.equal(view.sections[0].change_overview, "plugins.community.enabled")
})
