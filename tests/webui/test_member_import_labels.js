const test = require("node:test")
const assert = require("node:assert/strict")

const {
  dedupeStringList,
  localizedIssueLabels,
  isRawAstrBotImportItem,
  buildIssueSummary,
  importSourceLabel,
  buildImportSummaryText,
} = require("../../sharelife/webui/member_import_labels.js")

test("localizedIssueLabels keeps formatter output and dedupes blanks/duplicates", () => {
  const labels = localizedIssueLabels(["a", "a", "b"], {
    formatIssueLabels: () => ["A", "", "A", "B"],
  })
  assert.deepEqual(labels, ["A", "B"])
})

test("dedupeStringList normalizes mixed input", () => {
  assert.deepEqual(dedupeStringList(["", "a", "a", " b "]), ["a", "b"])
  assert.deepEqual(dedupeStringList("single"), ["single"])
})

test("buildIssueSummary renders preview and overflow count", () => {
  const summary = buildIssueSummary(["i1", "i2", "i3"], {
    limit: 2,
    formatIssueLabels: (values) => values.map((item) => item.toUpperCase()),
  })
  assert.equal(summary, "I1 · I2 +1")
})

test("importSourceLabel recognizes raw astrbot conversion issue", () => {
  const rawItem = { compatibility_issues: ["astrbot_raw_import_converted"] }
  const standardItem = { compatibility_issues: ["section_hash_mismatch:providers"] }

  assert.equal(isRawAstrBotImportItem(rawItem), true)
  assert.equal(isRawAstrBotImportItem(standardItem), false)
  assert.equal(
    importSourceLabel(rawItem, {
      rawLabel: "RAW",
      standardLabel: "STD",
    }),
    "RAW",
  )
  assert.equal(
    importSourceLabel(standardItem, {
      rawLabel: "RAW",
      standardLabel: "STD",
    }),
    "STD",
  )
})

test("buildImportSummaryText formats summary blocks with i18n formatter", () => {
  const formatted = buildImportSummaryText(
    {
      import_summary: {
        default_personality: "helper",
        persona_count: 3,
        subagent_count: 2,
        platform_count: 1,
        field_diagnostic_count: 4,
        field_diagnostic_outcomes: {
          mapped: 2,
          requires_manual_resolution: 1,
          omitted: 1,
        },
      },
    },
    {
      formatMessage: (key, fallback, tokens) => {
        if (key === "member.imports.summary_default_personality") return `P:${tokens.value}`
        if (key === "member.imports.summary_persona_count") return `N:${tokens.count}`
        if (key === "member.imports.summary_subagent_count") return `S:${tokens.count}`
        if (key === "member.imports.summary_platform_count") return `L:${tokens.count}`
        if (key === "member.imports.summary_field_diagnostic_count") return `D:${tokens.count}`
        if (key === "member.imports.summary_manual_review_count") return `M:${tokens.count}`
        return fallback
      },
    },
  )

  assert.equal(formatted, "P:helper · N:3 · S:2 · L:1 · D:4 · M:1")
})
