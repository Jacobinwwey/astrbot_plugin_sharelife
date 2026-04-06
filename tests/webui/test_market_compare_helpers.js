const test = require("node:test")
const assert = require("node:assert/strict")

const {
  resolveCompareChangeSummary,
  formatCompareSize,
  buildCompareDetailContent,
  emptyDetailMeta,
} = require("../../sharelife/webui/market_compare_helpers.js")

test("market compare helpers resolve change summary consistently", () => {
  assert.equal(resolveCompareChangeSummary({ file_path: "sections/core.json" }), "sections/core.json")
  assert.equal(resolveCompareChangeSummary({ section: "astrbot_core" }), "sections/astrbot_core.json")
  assert.equal(
    resolveCompareChangeSummary({ changed: true }, {
      i18nMessage(key, fallback) {
        return key || fallback
      },
    }),
    "market.compare.change_paths_fallback",
  )
  assert.equal(
    resolveCompareChangeSummary({ changed: false }, {
      i18nMessage(key, fallback) {
        return key || fallback
      },
    }),
    "market.compare.no_changes",
  )
})

test("market compare helpers format compact size text", () => {
  const text = formatCompareSize(
    { before_size: 10, after_size: 30, delta_size: 20 },
    {
      i18nMessage(key, fallback) {
        return key || fallback
      },
      i18nFormat(_key, fallback, tokens) {
        return String(fallback).replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, token) => String(tokens[token]))
      },
    },
  )
  assert.match(text, /10 \/ 30 \/ \+20/)
  assert.match(text, /market\.compare\.bytes/)
})

test("market compare helpers build detail content with preview fallbacks", () => {
  const detail = buildCompareDetailContent(
    {
      section: "astrbot_core",
      file_path: "sections/astrbot_core.json",
      diff_preview: [],
      before_preview: [],
      after_preview: [],
      before_hash_short: "abc123",
      after_hash_short: "def456",
      diff_preview_truncated: true,
      before_preview_truncated: true,
      after_preview_truncated: true,
    },
    {
      i18nMessage(key, fallback) {
        return key || fallback
      },
      i18nFormat(_key, fallback, tokens) {
        return String(fallback).replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, token) => String(tokens[token]))
      },
    },
  )
  assert.equal(detail.detailKey, "astrbot_core")
  assert.match(detail.metaText, /Section: astrbot_core/)
  assert.match(detail.metaText, /sections\/astrbot_core\.json/)
  assert.match(detail.diffText, /No unified diff preview/)
  assert.match(detail.diffText, /market\.compare\.detail\.truncated/)
  assert.match(detail.beforeText, /hash=abc123/)
  assert.match(detail.beforeText, /market\.compare\.detail\.truncated/)
  assert.match(detail.afterText, /hash=def456/)
  assert.match(detail.afterText, /market\.compare\.detail\.truncated/)
})

test("market compare helpers expose empty detail meta text", () => {
  const meta = emptyDetailMeta({
    i18nMessage(key, fallback) {
      return key || fallback
    },
  })
  assert.equal(meta, "market.compare.detail.empty_meta")
})
