const test = require("node:test")
const assert = require("node:assert/strict")
const fs = require("node:fs")
const path = require("node:path")

const REPO_ROOT = path.resolve(__dirname, "..", "..")

function readIfExists(relativePath) {
  const absolutePath = path.join(REPO_ROOT, relativePath)
  if (!fs.existsSync(absolutePath)) return ""
  return fs.readFileSync(absolutePath, "utf-8")
}

test("market action handlers keep legacy and detail button-id compatibility", () => {
  const source = [
    readIfExists("sharelife/webui/market_page.js"),
    readIfExists("sharelife/webui/market_event_bindings.js"),
  ].join("\n")

  assert.equal(Boolean(source.trim()), true)

  const requiredIdPairs = [
    ["btnMarketDetailRefreshInstallations", "btnMarketRefreshInstallations"],
    ["btnMarketDetailTrial", "btnMarketTemplateTrial"],
    ["btnMarketDetailInstall", "btnMarketTemplateInstall"],
    ["btnMarketDetailSubmitTemplate", "btnMarketTemplateSubmit"],
    ["btnMarketDetailSubmitProfilePack", "btnMarketProfilePackSubmit"],
  ]

  for (const [detailId, legacyId] of requiredIdPairs) {
    assert.equal(
      source.includes(detailId),
      true,
      `missing detail id compatibility marker: ${detailId}`,
    )
    assert.equal(
      source.includes(legacyId),
      true,
      `missing legacy id compatibility marker: ${legacyId}`,
    )
  }
})
