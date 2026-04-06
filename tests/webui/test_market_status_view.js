const test = require("node:test")
const assert = require("node:assert/strict")

const {
  buildSummaryText,
  buildEvidenceRows,
  renderDetailCards,
} = require("../../sharelife/webui/market_status_view.js")

test("market status view builds localized summary text", () => {
  const summary = buildSummaryText(
    {
      status: "updated",
      pack_id: "profile/official-safe-reference",
      template_id: "community/basic",
      submission_id: "sub-42",
      version: "1.0.1",
      featured: true,
      risk_level: "low",
      changed_sections_count: 3,
    },
    {
      i18nMessage(key) {
        return `i18n:${key}`
      },
      i18nFormat(_key, fallback, tokens) {
        return String(fallback).replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, token) => String(tokens[token]))
      },
      enumLabel(group, value) {
        return `${group}:${value}`
      },
      localizedPackLabel(packId) {
        return `pack:${packId}`
      },
    },
  )
  assert.match(summary, /status=status:updated/)
  assert.match(summary, /pack=pack:profile\/official-safe-reference/)
  assert.match(summary, /template=community\/basic/)
  assert.match(summary, /submission=sub-42/)
  assert.match(summary, /version=1.0.1/)
  assert.match(summary, /featured=i18n:option\.featured_toggle\.true/)
  assert.match(summary, /risk=risk:low/)
  assert.match(summary, /changed=3/)
})

test("market status view builds evidence rows including plugin execution groups", () => {
  const rows = buildEvidenceRows(
    {
      pack_id: "profile/demo",
      featured_note: "safe baseline",
      compatibility: "compatible",
      capability_summary: {
        declared: ["memory", "tools"],
      },
      review_evidence: {
        review_labels: ["approved", "official_featured"],
      },
      plugin_install: {
        status: "failed",
        latest_execution: {
          attempt_count: 2,
        },
      },
    },
    {
      i18nMessage(key, fallback) {
        return key || fallback
      },
      i18nFormat(_key, fallback, tokens) {
        return String(fallback).replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, token) => String(tokens[token]))
      },
      enumLabel(group, value) {
        return `${group}:${value}`
      },
      localizedPackFeaturedNote(packId, value) {
        return `${packId}:${value}`
      },
      localizedList(_group, values) {
        return Array.isArray(values) ? values.join(", ") : "-"
      },
      summarizePluginInstallExecution() {
        return {
          status: "failed",
          installed_count: 1,
          failed_count: 2,
          blocked_count: 1,
          groups: {
            policy_blocked: ["pluginA"],
            command_failed: ["pluginB"],
            timed_out: ["pluginC"],
          },
        }
      },
    },
  )
  assert.equal(rows.length, 7)
  assert.equal(rows[0].value, "profile/demo:safe baseline")
  assert.equal(rows[1].value, "compatibility:compatible")
  assert.equal(rows[4].value, "plugin_install_status:failed")
  assert.match(rows[5].value, /installed=1, failed=2, blocked=1/)
  assert.match(rows[6].value, /profile_pack\.review\.group\.policy_blocked: pluginA/)
  assert.match(rows[6].value, /profile_pack\.review\.group\.command_failed: pluginB/)
  assert.match(rows[6].value, /profile_pack\.review\.group\.timed_out: pluginC/)
})

test("market status view renders rows as detail cards", () => {
  const created = []
  const document = {
    createElement() {
      const node = {
        className: "",
        textContent: "",
        children: [],
        appendChild(child) {
          this.children.push(child)
        },
      }
      created.push(node)
      return node
    },
  }
  const root = {
    innerHTML: "seed",
    children: [],
    appendChild(child) {
      this.children.push(child)
    },
    ownerDocument: document,
  }
  renderDetailCards(root, [{ label: "risk", value: "low" }], { document })
  assert.equal(root.innerHTML, "")
  assert.equal(root.children.length, 1)
  assert.equal(root.children[0].className, "detail-card")
  assert.equal(created.length >= 3, true)
})
