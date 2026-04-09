const assert = require("node:assert/strict")
const fs = require("node:fs")
const path = require("node:path")

const { chromium } = require("playwright")

const baseUrl = process.env.SHARELIFE_WEBUI_URL || "http://127.0.0.1:38107"
const artifactDir = process.env.SHARELIFE_E2E_ARTIFACT_DIR || path.resolve(process.cwd(), "output/playwright")

async function main() {
  fs.mkdirSync(artifactDir, { recursive: true })

  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
    chromiumSandbox: false,
  })
  const page = await browser.newPage()

  try {
    await page.goto(`${baseUrl}/market`, { waitUntil: "networkidle" })
    await page.waitForFunction(() => {
      const authPanel = document.querySelector("#marketAuthPanel")
      const roleNode = document.querySelector("#marketAuthRole")
      return Boolean(
        authPanel &&
          roleNode &&
          !authPanel.classList.contains("hidden") &&
          roleNode.disabled &&
          String(roleNode.value || "") === "member",
      )
    })

    assert.equal(await page.locator("#marketAuthPassword").isVisible(), true)
    await page.fill("#marketAuthPassword", "member-secret")
    await page.click("#btnMarketLogin")

    await page.waitForFunction(() => {
      const roleLine = String(document.querySelector("#marketRoleLine")?.textContent || "")
      return /role:\s*member/i.test(roleLine)
    })

    await page.waitForFunction(() => {
      const cards = document.querySelectorAll("#marketCatalogGrid .template-card")
      return cards.length >= 1
    })

    const token = await page.evaluate(async () => {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: "member",
          password: "member-secret",
        }),
      })
      const payload = await response.json().catch(() => ({}))
      if (!payload || payload.ok !== true) return ""
      return String(payload.token || "")
    })
    assert.equal(Boolean(token), true)

    const mismatchStatus = await page.evaluate(async (bearerToken) => {
      const denied = await fetch("/api/member/submissions?user_id=other-member", {
        headers: { Authorization: `Bearer ${bearerToken}` },
      })
      return denied.status
    }, token)
    assert.equal(mismatchStatus, 403)

    const ownerStatus = await page.evaluate(async (bearerToken) => {
      const allowed = await fetch("/api/member/submissions?user_id=webui-user", {
        headers: { Authorization: `Bearer ${bearerToken}` },
      })
      return allowed.status
    }, token)
    assert.equal(ownerStatus, 200)
  } finally {
    const shotPath = path.join(artifactDir, "sharelife-market-auth-e2e.png")
    await page.screenshot({ path: shotPath, fullPage: true }).catch(() => {})
    await browser.close()
  }
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
