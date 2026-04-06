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

    assert.equal(await page.locator("#marketAuthUserId").isVisible(), true)
    await page.fill("#marketAuthUserId", "member-auth-e2e")
    await page.fill("#marketAuthPassword", "member-secret")
    await page.click("#btnMarketLogin")

    await page.waitForFunction(() => {
      const roleLine = String(document.querySelector("#marketRoleLine")?.textContent || "")
      return /role:\s*member/i.test(roleLine)
    })

    await page.fill("#marketTemplateId", "community/auth-market")
    if (await page.locator("#marketSubmitVersion").count()) {
      await page.fill("#marketSubmitVersion", "1.0.0")
    }
    await page.click("#btnMarketTemplateSubmit")

    await page.click("#btnMarketListSubmissions")
    await page.waitForFunction(() => {
      const state = String(document.querySelector("#marketSubmissionsState")?.textContent || "")
      if (/Failed to load/i.test(state)) return false
      const rows = document.querySelectorAll("#marketSubmissionsList .member-task-item")
      return rows.length >= 1
    })
    const targetRow = page.locator("#marketSubmissionsList .member-task-item", { hasText: "community/auth-market" }).first()
    await targetRow.click()

    await page.waitForFunction(() => {
      const details = String(document.querySelector("#marketDetails")?.textContent || "")
      return /"template_id":\s*"community\/auth-market"/.test(details) && /"user_id":\s*"member-auth-e2e"/.test(details)
    })

    const token = await page.evaluate(async () => {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: "member",
          user_id: "member-auth-e2e",
          password: "member-secret",
        }),
      })
      const payload = await response.json().catch(() => ({}))
      if (!payload || payload.ok !== true) return ""
      return String(payload.token || "")
    })
    assert.equal(Boolean(token), true)

    const mismatchStatus = await page.evaluate(async (bearerToken) => {
      const denied = await fetch("/api/member/submissions?user_id=webui-user", {
        headers: { Authorization: `Bearer ${bearerToken}` },
      })
      return denied.status
    }, token)
    assert.equal(mismatchStatus, 403)

    const ownerStatus = await page.evaluate(async (bearerToken) => {
      const allowed = await fetch("/api/member/submissions?user_id=member-auth-e2e", {
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
