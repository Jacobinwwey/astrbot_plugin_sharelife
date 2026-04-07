const assert = require("node:assert/strict")
const fs = require("node:fs")
const path = require("node:path")

const { chromium } = require("playwright")

const baseUrl = process.env.SHARELIFE_WEBUI_URL || "http://127.0.0.1:38106"
const artifactDir = process.env.SHARELIFE_E2E_ARTIFACT_DIR || path.resolve(process.cwd(), "output/playwright")

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function text(page, selector) {
  return String((await page.locator(selector).textContent()) || "").trim()
}

async function waitForProfilePackDryrunReady(page) {
  await page.waitForFunction(() => {
    const summary = String(document.querySelector("#profilePackSummary")?.textContent || "")
    const details = String(document.querySelector("#profilePackDetails")?.textContent || "")
    return (
      /status=dryrun(?:_| )ready/i.test(summary) ||
      /"status"\s*:\s*"dryrun_ready"/i.test(details)
    )
  })
}

async function main() {
  fs.mkdirSync(artifactDir, { recursive: true })

  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
    chromiumSandbox: false,
  })
  const page = await browser.newPage()

  try {
    await page.goto(`${baseUrl}/member`, { waitUntil: "networkidle" })
    await page.waitForFunction(() => {
      const role = document.querySelector("#role")
      const authRole = document.querySelector("#authRole")
      if (!role || !authRole) return false
      const options = Array.from(authRole.options || []).map((item) => String(item.value || ""))
      return (
        role.disabled &&
        String(role.value || "") === "member" &&
        authRole.disabled &&
        options.length === 1 &&
        options[0] === "member"
      )
    })
    assert.equal(await page.locator("#memberConsoleLink").isVisible(), true)
    assert.equal(await page.locator("#marketConsoleLink").isVisible(), true)
    assert.equal(await page.locator("#adminConsoleLink").isVisible(), false)
    assert.equal(await page.locator("#reviewerConsoleLink").isVisible(), false)
    assert.equal(await page.locator("#btnToggleDeveloperMode").isVisible(), false)
    assert.equal(await page.locator("#memberSpotlightShell").isVisible(), true)
    assert.equal(await page.locator('[data-i18n-key="market.hub.heading"]').count(), 0)
    assert.equal(await page.locator("#memberUploadDropzone").isVisible(), true)
    await page.waitForFunction(() => {
      const node = document.querySelector("#memberInstallationsState")
      return node && /Local installations:|No local installations yet\./i.test(String(node.textContent || ""))
    })
    await page.click("#btnRefreshMemberInstallations")
    await page.waitForFunction(() => {
      const node = document.querySelector("#memberInstallationsState")
      return node && /Local installations:/i.test(String(node.textContent || ""))
    })
    await page.fill("#memberGlobalSearch", "community/basic")
    await page.waitForFunction(() => {
      const section = document.querySelector("#section-market")
      const filter = document.querySelector("#templateFilterId")
      const cards = document.querySelectorAll("#templateCardGrid .template-card")
      return (
        section &&
        !section.classList.contains("hidden") &&
        filter &&
        String(filter.value || "") === "community/basic" &&
        cards.length >= 1
      )
    })
    await page.fill("#memberGlobalSearch", "profile/official-starter")
    await page.waitForFunction(() => {
      const button = document.querySelector("#memberSpotlightMarketJump")
      return (
        button &&
        !button.classList.contains("hidden") &&
        /profile\/official-starter/i.test(String(button.getAttribute("data-market-query") || ""))
      )
    })
    await page.click("#memberSpotlightMarketJump")
    await page.waitForURL(/\/market\?q=profile%2Fofficial-starter/)
    await page.waitForFunction(() => {
      const input = document.querySelector("#marketGlobalSearch")
      return input && String(input.value || "").trim() === "profile/official-starter"
    })

    await page.goto(`${baseUrl}/market`, { waitUntil: "networkidle" })
    await page.waitForFunction(() => {
      const member = document.querySelector("#marketMemberConsoleLink")
      const reviewer = document.querySelector("#marketReviewerConsoleLink")
      const admin = document.querySelector("#marketAdminConsoleLink")
      const full = document.querySelector("#marketFullConsoleLink")
      const authPanel = document.querySelector("#marketAuthPanel")
      if (!member || !reviewer || !admin || !full || !authPanel) return false
      return (
        !member.classList.contains("hidden") &&
        reviewer.classList.contains("hidden") &&
        admin.classList.contains("hidden") &&
        full.classList.contains("hidden") &&
        authPanel.classList.contains("hidden")
      )
    })
    assert.equal(await page.locator("#marketMemberConsoleLink").isVisible(), true)
    assert.equal(await page.locator("#marketReviewerConsoleLink").isVisible(), false)
    assert.equal(await page.locator("#marketAdminConsoleLink").isVisible(), false)
    assert.equal(await page.locator("#marketFullConsoleLink").isVisible(), false)

    await page.goto(`${baseUrl}/reviewer`, { waitUntil: "networkidle" })
    await page.waitForFunction(() => {
      const role = document.querySelector("#role")
      const authRole = document.querySelector("#authRole")
      const authPanel = document.querySelector("#authPanel")
      const readonlyNotice = document.querySelector("#reviewerReadonlyNotice")
      const adminLinkedNotice = document.querySelector("#reviewerAdminLinkedNotice")
      const developerToggle = document.querySelector("#btnToggleDeveloperMode")
      const listSubmissions = document.querySelector("#btnListSubmissions")
      if (!role || !authRole || !authPanel || !readonlyNotice || !adminLinkedNotice || !developerToggle || !listSubmissions) {
        return false
      }
      const options = Array.from(authRole.options || []).map((item) => String(item.value || ""))
      return (
        role.disabled &&
        String(role.value || "") === "member" &&
        authRole.disabled &&
        options.length === 1 &&
        options[0] === "member" &&
        authPanel.classList.contains("hidden") &&
        !readonlyNotice.classList.contains("hidden") &&
        adminLinkedNotice.classList.contains("hidden") &&
        developerToggle.classList.contains("hidden") &&
        listSubmissions.disabled
      )
    })
    assert.equal(await page.locator("#reviewerReadonlyNotice").isVisible(), true)
    assert.equal(await page.locator("#reviewerAdminLinkedNotice").isVisible(), false)
    assert.equal(await page.locator("#btnToggleDeveloperMode").isVisible(), false)

    await page.goto(`${baseUrl}/admin`, { waitUntil: "networkidle" })
    await page.waitForFunction(() => {
      const role = document.querySelector("#role")
      const authRole = document.querySelector("#authRole")
      if (!role || !authRole) return false
      const options = Array.from(authRole.options || []).map((item) => String(item.value || ""))
      return (
        role.disabled &&
        String(role.value || "") === "admin" &&
        authRole.disabled &&
        options.length === 1 &&
        options[0] === "admin"
      )
    })
    assert.equal(await page.locator("#memberConsoleLink").isVisible(), true)
    assert.equal(await page.locator("#adminConsoleLink").isVisible(), false)
    await page.click("#btnToggleDeveloperMode")
    await page.waitForFunction(() => /Developer mode:\s*on/i.test(String(document.querySelector("#developerModeLine")?.textContent || "")))
    await page.evaluate(() => {
      const details = document.querySelector("#section-reliability details")
      if (details) details.open = true
    })
    await page.click("#btnAudit")
    await page.waitForFunction(() => {
      const summary = document.querySelector("#auditSummaryOutput")
      const events = document.querySelector("#auditEventsOutput")
      return (
        summary &&
        events &&
        /Audit Summary|审计摘要|監査サマリー/i.test(String(summary.textContent || "")) &&
        /Recent Events|最近事件|最新イベント/i.test(String(events.textContent || ""))
      )
    })
    await page.click("#btnToggleDeveloperMode")
    await page.waitForFunction(() => /Developer mode:\s*off/i.test(String(document.querySelector("#developerModeLine")?.textContent || "")))

    await page.goto(baseUrl, { waitUntil: "networkidle" })

    assert.match(await text(page, "#workspaceRoute"), /route: idle/i)
    assert.match(await text(page, "#templateListState"), /Load templates/i)
    assert.match(await text(page, "#submissionListState"), /Load submissions/i)
    assert.match(await text(page, "#templateDetailState"), /Select a template row/i)
    assert.match(await text(page, "#submissionDetailState"), /Select a submission row/i)
    assert.equal(
      await page.locator(".workspace-context-actions").evaluate((node) => node.hasAttribute("open")),
      false,
    )
    assert.equal(
      await page.locator("#section-risk-glossary details").evaluate((node) => node.hasAttribute("open")),
      false,
    )

    await page.click('[data-locale-option="zh-CN"]')
    await page.waitForFunction(() => String(document.querySelector("#uiLocale")?.value || "") === "zh-CN")
    assert.match(await text(page, '[data-i18n-key="profile_pack.market.title"]'), /社区市场/i)
    await page.click('[data-locale-option="en-US"]')
    await page.waitForFunction(() => String(document.querySelector("#uiLocale")?.value || "") === "en-US")
    assert.match(await text(page, '[data-i18n-key="profile_pack.market.title"]'), /Profile Pack Market/i)

    await page.selectOption("#uiLocale", "zh-CN")
    await page.waitForFunction(() => {
      const title = String(document.querySelector('[data-i18n-key="profile_pack.market.title"]')?.textContent || "")
      return /社区市场/.test(title)
    })
    assert.match(await text(page, "#templateListState"), /加载模板列表/i)
    assert.match(await text(page, "#submissionListState"), /加载投稿列表/i)
    assert.match(await text(page, "#workspaceSummary"), /持久化工作区路由/i)
    assert.match(await text(page, "#templateWorkspaceRoute"), /模板工作区空闲/i)
    assert.match(await text(page, "#compareState"), /选择投稿行以加载对比结果/i)
    assert.match(await text(page, "#moderationSummary"), /选择投稿行以回填审核字段/i)
    assert.match(await text(page, '[data-i18n-key="panel.moderation.heading"]'), /审核工作区/i)
    assert.match(await text(page, '[data-i18n-key="panel.scan.heading"]'), /风险扫描/i)
    assert.match(await text(page, "#profilePackSubmissionState"), /加载 profile-pack 投稿/i)
    assert.match(await text(page, "#profilePackCatalogState"), /加载 profile-pack 目录/i)

    await page.selectOption("#uiLocale", "ja-JP")
    await page.waitForFunction(() => {
      const title = String(document.querySelector('[data-i18n-key="profile_pack.market.title"]')?.textContent || "")
      return /マーケット/.test(title)
    })
    assert.match(await text(page, "#btnProfilePackSubmitCommunity"), /コミュニティへ投稿/i)

    await page.reload({ waitUntil: "networkidle" })
    assert.equal(String(await page.locator("#uiLocale").inputValue()).trim(), "ja-JP")
    assert.match(await text(page, '[data-i18n-key="profile_pack.market.title"]'), /マーケット/i)

    await page.evaluate(() => {
      localStorage.setItem("sharelife.uiLocale", "fr-FR")
    })
    await page.reload({ waitUntil: "networkidle" })
    assert.equal(String(await page.locator("#uiLocale").inputValue()).trim(), "en-US")
    assert.match(await text(page, '[data-i18n-key="profile_pack.market.title"]'), /Profile Pack Market/i)
    assert.match(await text(page, "#templateListState"), /Load templates/i)
    assert.match(await text(page, "#submissionListState"), /Load submissions/i)
    assert.match(await text(page, "#workspaceSummary"), /persistent workspace route/i)
    assert.match(await text(page, "#compareState"), /Select a submission row to load compare output/i)
    assert.match(await text(page, "#moderationSummary"), /Select a submission row to hydrate review fields/i)
    assert.match(await text(page, '[data-i18n-key="panel.moderation.heading"]'), /Moderation/i)
    assert.match(await text(page, "#scanSummary"), /No package scan loaded yet/i)

    const templatesListDelay = async (route) => {
      await delay(300)
      await route.continue()
    }
    const templateDelay = async (route) => {
      await delay(300)
      await route.continue()
    }
    await page.route(/\/api\/templates(?:\?.*)?$/, templatesListDelay)
    await page.route("**/api/templates/detail**", templateDelay)

    await page.click("#btnTemplates")
    await page.waitForFunction(() => {
      const node = document.querySelector("#templateListState")
      return node && !node.classList.contains("hidden") && /Loading Templates/i.test(node.textContent || "")
    })
    await page.waitForSelector('tr[data-template-id="community/basic"]')
    await page.waitForFunction(() => document.querySelector("#templateListState")?.classList.contains("hidden"))
    await page.waitForSelector("#templateCardGrid .template-card")
    await page.waitForFunction(() => {
      const featuredState = document.querySelector("#featuredTemplateState")
      const trendingState = document.querySelector("#trendingTemplateState")
      const featuredCard = document.querySelector("#featuredTemplateCard .featured-template-entry")
      const trendingItems = document.querySelectorAll("#trendingTemplateList .trending-template-item")
      return (
        featuredState &&
        trendingState &&
        featuredState.classList.contains("hidden") &&
        trendingState.classList.contains("hidden") &&
        featuredCard &&
        trendingItems.length >= 1
      )
    })

    const firstTemplateCard = page.locator("#templateCardGrid .template-card").first()
    await firstTemplateCard.click()
    await page.waitForFunction(() => {
      const drawer = document.querySelector("#templateDrawer")
      const title = document.querySelector("#templateDrawerTitle")
      return (
        drawer &&
        !drawer.classList.contains("hidden") &&
        title &&
        /community\/basic/i.test(String(title.textContent || ""))
      )
    })
    assert.equal(String(await page.evaluate(() => document.activeElement?.id || "")).trim(), "btnTemplateDrawerClose")
    await page.keyboard.press("Escape")
    await page.waitForFunction(() => document.querySelector("#templateDrawer")?.classList.contains("hidden"))
    await page.waitForFunction(() => {
      const drawer = document.querySelector("#templateDrawer")
      const node = document.activeElement
      return Boolean(drawer && (!node || !drawer.contains(node)))
    })

    await page.click("#btnOpenSubmitWizard")
    await page.waitForFunction(() => {
      const modal = document.querySelector("#submitWizardModal")
      return modal && !modal.classList.contains("hidden")
    })
    assert.equal(String(await page.evaluate(() => document.activeElement?.id || "")).trim(), "wizardTemplateId")
    await page.keyboard.press("Escape")
    await page.waitForFunction(() => {
      const modal = document.querySelector("#submitWizardModal")
      return modal && modal.classList.contains("hidden")
    })
    assert.equal(String(await page.evaluate(() => document.activeElement?.id || "")).trim(), "btnOpenSubmitWizard")

    await page.click("#btnOpenSubmitWizard")
    await page.waitForFunction(() => {
      const modal = document.querySelector("#submitWizardModal")
      return modal && !modal.classList.contains("hidden")
    })
    await page.fill("#wizardTemplateId", "community/wizard-e2e")
    await page.fill("#wizardTemplateVersion", "1.9.0")
    await page.click("#btnSubmitWizardNext")
    await page.waitForFunction(() => {
      const step = document.querySelector('#submitWizardModal .wizard-step[data-step="2"]')
      return step && !step.classList.contains("hidden")
    })
    await page.click("#btnSubmitWizardNext")
    await page.waitForFunction(() => {
      const step = document.querySelector('#submitWizardModal .wizard-step[data-step="3"]')
      const review = document.querySelector("#submitWizardReview")
      return (
        step &&
        !step.classList.contains("hidden") &&
        review &&
        /community\/wizard-e2e/i.test(String(review.textContent || ""))
      )
    })
    await page.click("#btnSubmitWizardPublish")
    await page.waitForFunction(() => {
      const modal = document.querySelector("#submitWizardModal")
      return modal && modal.classList.contains("hidden")
    })
    assert.equal(String(await page.locator("#submitTemplateId").inputValue()).trim(), "community/wizard-e2e")
    assert.equal(String(await page.locator("#trialTemplateId").inputValue()).trim(), "community/wizard-e2e")
    await page.waitForFunction(() => /submit_template_wizard/i.test(String(document.querySelector("#result")?.textContent || "")))
    await page.waitForSelector('tr[data-template-id="community/basic"]')
    await page.waitForSelector("#templateCardGrid .template-card")

    await page.fill("#templateFilterId", "missing/template")
    await page.click("#btnTemplates")
    await page.waitForFunction(() => {
      const node = document.querySelector("#templateListState")
      return node && !node.classList.contains("hidden") && /No templates matched/i.test(node.textContent || "")
    })
    await page.fill("#templateFilterId", "")
    await page.click("#btnTemplates")
    await page.waitForSelector('tr[data-template-id="community/basic"]')
    await page.waitForFunction(() => document.querySelector("#templateListState")?.classList.contains("hidden"))

    await page.locator('tr[data-template-id="community/basic"] td').first().click()

    await page.waitForFunction(() => {
      const node = document.querySelector("#templateDetailState")
      return node && !node.classList.contains("hidden") && /Loading Template detail/i.test(node.textContent || "")
    })
    await page.waitForFunction(() => location.hash.includes("scope=template"))
    await page.waitForFunction(() => {
      const node = document.querySelector("#templateDetailSummary")
      return node && /community\/basic@1\.0\.0/.test(node.textContent || "")
    })
    await page.waitForFunction(() => document.querySelector("#templateDetailState")?.classList.contains("hidden"))
    await page.unroute("**/api/templates/detail**", templateDelay)

    await page.goto(`${baseUrl}/#scope=template&id=missing%2Ftemplate`, { waitUntil: "networkidle" })
    await page.waitForFunction(() => {
      const node = document.querySelector("#templateDetailState")
      return node && !node.classList.contains("hidden") && /failed:/i.test(node.textContent || "")
    })
    assert.match(await text(page, "#templateDetailState"), /Template detail failed:/i)

    await page.goto(baseUrl, { waitUntil: "networkidle" })
    const memberCapabilities = await page.evaluate(async () => {
      const response = await fetch("/api/ui/capabilities?role=member")
      return response.json()
    })
    assert.equal(memberCapabilities.ok, true)
    assert.equal(memberCapabilities.role, "member")
    assert.equal(memberCapabilities.operations.includes("templates.list"), true)
    assert.equal(memberCapabilities.operations.includes("admin.apply.workflow"), false)

    const adminCapabilities = await page.evaluate(async () => {
      const response = await fetch("/api/ui/capabilities?role=admin")
      return response.json()
    })
    assert.equal(adminCapabilities.ok, true)
    assert.equal(adminCapabilities.role, "admin")
    assert.equal(adminCapabilities.operations.includes("admin.apply.workflow"), true)

    assert.equal(await page.locator("#btnListSubmissions").isVisible(), false)
    await page.selectOption("#role", "admin")
    await page.waitForFunction(() => {
      const node = document.querySelector("#btnListSubmissions")
      return Boolean(node) && !node.closest(".hidden")
    })
    assert.equal(await page.locator("#btnListSubmissions").isDisabled(), false)
    await page.evaluate(() => {
      const details = document.querySelector("#section-storage-backup details")
      if (details) details.open = true
    })
    await page.click("#btnStorageSummary")
    await page.waitForFunction(() => {
      const node = document.querySelector("#storageSummaryOutput")
      return node && /Storage root:/i.test(String(node.textContent || ""))
    })

    await page.click("#btnStoragePoliciesGet")
    await page.waitForFunction(() => {
      const node = document.querySelector("#storagePoliciesOutput")
      return node && /rpo_hours=/i.test(String(node.textContent || ""))
    })
    await page.fill("#storagePolicyRpoHours", "12")
    await page.click("#btnStoragePoliciesSet")
    await page.waitForFunction(() => {
      const node = document.querySelector("#storagePoliciesOutput")
      return node && /rpo_hours=12/i.test(String(node.textContent || ""))
    })

    await page.fill("#storageJobTrigger", "e2e")
    await page.fill("#storageJobNote", "playwright e2e backup")
    await page.click("#btnStorageRunBackup")
    await page.waitForFunction(() => {
      const input = document.querySelector("#storageJobId")
      return Boolean(input && String(input.value || "").trim())
    })
    const storageJobId = String(await page.locator("#storageJobId").inputValue()).trim()
    assert.match(storageJobId, /^backup-/i)

    await page.click("#btnStorageJobGet")
    await page.waitForFunction(() => {
      const node = document.querySelector("#storageJobsOutput")
      return node && /Backup Job Detail/i.test(String(node.textContent || ""))
    })
    await page.waitForFunction(() => {
      const input = document.querySelector("#storageRestoreArtifactRef")
      return Boolean(input && String(input.value || "").trim())
    })

    await page.click("#btnStorageRestorePrepare")
    await page.waitForFunction(() => {
      const input = document.querySelector("#storageRestoreId")
      return Boolean(input && String(input.value || "").trim())
    })
    const restoreId = String(await page.locator("#storageRestoreId").inputValue()).trim()
    assert.match(restoreId, /^restore-/i)

    await page.click("#btnStorageRestoreJobsList")
    await page.waitForFunction(() => {
      const node = document.querySelector("#storageRestoreJobsOutput")
      return node && /Restore Jobs/i.test(String(node.textContent || ""))
    })
    await page.fill("#storageRestoreJobId", restoreId)
    await page.click("#btnStorageRestoreJobGet")
    await page.waitForFunction(() => {
      const node = document.querySelector("#storageRestoreJobsOutput")
      return node && /Restore Detail/i.test(String(node.textContent || ""))
    })
    await page.click("#btnStorageRestoreCommit")
    await page.waitForFunction(() => {
      const node = document.querySelector("#storageRestoreOutput")
      return node && /state=committed/i.test(String(node.textContent || ""))
    })

    assert.equal(
      await page.locator("#profilePackPluginInstallAdvanced").evaluate((node) => node.hasAttribute("open")),
      false,
    )
    assert.match(await text(page, "#profilePackSummary"), /No profile pack operation yet/i)

    await page.click("#btnProfilePackExport")
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackSummary")
      return node && /status=exported/i.test(node.textContent || "")
    })
    const artifactId = String(await page.locator("#profilePackImportArtifactId").inputValue()).trim()
    assert.ok(artifactId)

    await page.fill("#profilePackImportArtifactId", artifactId)
    await page.click("#btnProfilePackImportFromExport")
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackSummary")
      return node && /status=imported/i.test(node.textContent || "")
    })
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackCompatibilitySummary")
      return node && /Compatibility:/i.test(String(node.textContent || ""))
    })
    assert.doesNotMatch(
      await text(page, "#profilePackCompatibilitySummary"),
      /No compatibility guidance yet/i,
    )
    await page.evaluate(() => {
      if (typeof window.updateProfilePackPanel !== "function") {
        throw new Error("updateProfilePackPanel is unavailable")
      }
      window.updateProfilePackPanel({
        status: "imported",
        pack_id: "profile/e2e-shortcut",
        compatibility: "degraded",
        missing_plugins: ["community_tools"],
        plugin_install: {
          status: "confirmation_required",
          required_plugins: ["community_tools"],
          missing_plugins: ["community_tools"],
        },
        compatibility_issues: [
          "environment_plugin_binary_reconfigure_required",
          "knowledge_base_storage_sync_required",
        ],
      })
    })
    await page.waitForSelector(
      '#profilePackCompatibilityActions .warning-action-button[data-action-code="reconfigure_plugin_binary"]',
    )
    await page.click(
      '#profilePackCompatibilityActions .warning-action-button[data-action-code="reconfigure_plugin_binary"]',
    )
    await page.waitForFunction(() => {
      const details = document.querySelector("#profilePackPluginInstallAdvanced")
      return Boolean(details && details.open)
    })
    await page.waitForFunction(() => {
      const input = document.querySelector("#profilePackPluginIds")
      return input && String(input.value || "").includes("community_tools")
    })
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackCompatibilityActionStatus")
      return node && /plugin install controls/i.test(String(node.textContent || ""))
    })
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackCompatibilityActionStatus")
      return node && /Prefill applied/i.test(String(node.textContent || ""))
    })
    await page.click(
      '#profilePackCompatibilityActions .warning-action-button[data-action-code="tell_ai_reconfigure_environment"]',
    )
    await page.click(
      '#profilePackCompatibilityIssues .warning-issue-button[data-issue-code="environment_plugin_binary_reconfigure_required"]',
    )
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackCompatibilityActionStatus")
      return node && /plugin install controls/i.test(String(node.textContent || ""))
    })
    await page.click(
      '#profilePackCompatibilityIssues .warning-issue-button[data-issue-code="knowledge_base_storage_sync_required"]',
    )
    await page.waitForFunction(() => {
      const checkbox = document.querySelector('input[data-profile-section="knowledge_base"]')
      if (!checkbox) return false
      const sections = String(document.querySelector("#profilePackSections")?.value || "")
      return checkbox.checked && sections.includes("knowledge_base")
    })
    await page.click(
      '#profilePackCompatibilityActions .warning-action-button[data-action-code="tell_ai_reconfigure_environment"]',
    )
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackCompatibilityActionStatus")
      return node && /continue automatically/i.test(String(node.textContent || ""))
    })
    await page.click("#btnToggleDeveloperMode")
    await page.waitForFunction(() => /Developer mode:\s*on/i.test(String(document.querySelector("#developerModeLine")?.textContent || "")))
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackCompatibilityDeveloper")
      return node && !node.classList.contains("hidden") && /compatibility/i.test(String(node.textContent || ""))
    })
    await page.waitForFunction(() => {
      const status = document.querySelector("#profilePackCompatibilityActionStatus")
      return Boolean(
        status && /raw compatibility payload/i.test(String(status.textContent || "")),
      )
    })
    await page.click("#btnToggleDeveloperMode")
    await page.waitForFunction(() => /Developer mode:\s*off/i.test(String(document.querySelector("#developerModeLine")?.textContent || "")))
    const importedId = String(await page.locator("#profilePackImportId").inputValue()).trim()
    assert.ok(importedId)

    await page.fill("#profilePackPlanId", "profile-plan-e2e")
    const profileImportDryrunDelay = async (route) => {
      await delay(300)
      await route.continue()
    }
    await page.route("**/api/admin/profile-pack/import-and-dryrun**", profileImportDryrunDelay)
    await page.click("#btnProfilePackImportDryrun")
    await waitForProfilePackDryrunReady(page)
    assert.match(await text(page, "#profilePackSummary"), /plan=profile-plan-e2e/i)
    await page.unroute("**/api/admin/profile-pack/import-and-dryrun**", profileImportDryrunDelay)

    await page.fill("#profilePackId", "profile/research")
    await page.fill("#profilePackVersion", "2.0.0")
    await page.click("#btnProfilePackExport")
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackSummary")
      return node && /status=exported/i.test(node.textContent || "")
    })
    const researchArtifactId = String(await page.locator("#profilePackImportArtifactId").inputValue()).trim()
    assert.ok(researchArtifactId)
    assert.notEqual(researchArtifactId, artifactId)

    await page.fill("#profilePackImportArtifactId", researchArtifactId)
    await page.click("#btnProfilePackImportFromExport")
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackSummary")
      return node && /status=imported/i.test(node.textContent || "")
    })
    const researchImportId = String(await page.locator("#profilePackImportId").inputValue()).trim()
    assert.ok(researchImportId)
    assert.notEqual(researchImportId, importedId)

    await page.click("#btnProfilePackListImports")
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackRecords")
      return node && /Use \+ Dry-Run/i.test(node.textContent || "")
    })
    await page.click("#btnProfilePackListExports")
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackRecords")
      return node && /Use \+ Import/i.test(node.textContent || "")
    })

    await page.fill("#profilePackRecordPackFilter", "profile/research")
    await page.waitForFunction(() => {
      const heads = Array.from(document.querySelectorAll("#profilePackRecords .profile-pack-record-head"))
      return heads.length >= 2 && heads.every((node) => String(node.textContent || "").includes("profile/research"))
    })
    const selectedExportHeadText = String(
      await page
        .locator('#profilePackRecords .profile-pack-record-group[data-group="exports"] .profile-pack-record-head')
        .first()
        .textContent(),
    ).trim()
    const selectedExportArtifactId = selectedExportHeadText.split("|")[0].trim()

    await page.fill("#profilePackImportArtifactId", "")
    await page.fill("#profilePackPlanId", "")
    await page
      .locator('#profilePackRecords .profile-pack-record-group[data-group="exports"] .record-action-button[data-action-id="use"]')
      .first()
      .click()
    assert.equal(
      String(await page.locator("#profilePackImportArtifactId").inputValue()).trim(),
      selectedExportArtifactId || researchArtifactId,
    )
    assert.match(String(await page.locator("#profilePackPlanId").inputValue()).trim(), /^profile-plan-/)

    await page.click(
      '#profilePackRecords .profile-pack-record-group[data-group="exports"] .record-action-button[data-action-id="use_import"]',
    )
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackSummary")
      return node && /status=imported/i.test(node.textContent || "")
    })

    await page.click(
      '#profilePackRecords .profile-pack-record-group[data-group="exports"] .record-action-button[data-action-id="use_dryrun"]',
    )
    await waitForProfilePackDryrunReady(page)

    await page.fill("#profilePackImportId", "")
    await page.fill("#profilePackPlanId", "")
    const selectedImportHeadText = String(
      await page
        .locator('#profilePackRecords .profile-pack-record-group[data-group="imports"] .profile-pack-record-head')
        .first()
        .textContent(),
    ).trim()
    const selectedImportId = selectedImportHeadText.split("|")[0].trim()
    await page
      .locator('#profilePackRecords .profile-pack-record-group[data-group="imports"] .record-action-button[data-action-id="use"]')
      .first()
      .click()
    assert.equal(
      String(await page.locator("#profilePackImportId").inputValue()).trim(),
      selectedImportId || researchImportId,
    )
    assert.match(String(await page.locator("#profilePackPlanId").inputValue()).trim(), /^profile-plan-/)

    await page.click(
      '#profilePackRecords .profile-pack-record-group[data-group="imports"] .record-action-button[data-action-id="use_dryrun"]',
    )
    await waitForProfilePackDryrunReady(page)

    await page.fill("#profilePackRecordPackFilter", "__no_match__")
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackRecords")
      return node && /No profile pack records matched current pack_id filter/i.test(node.textContent || "")
    })
    await page.fill("#profilePackRecordPackFilter", "")

    await page.fill("#profilePackSubmissionArtifactId", researchArtifactId)
    await page.click("#btnProfilePackSubmitCommunity")
    await page.waitForFunction(() => {
      const value = String(document.querySelector("#profilePackDecisionSubmissionId")?.value || "").trim()
      return value.length > 0
    })
    const profileSubmissionId = String(await page.locator("#profilePackDecisionSubmissionId").inputValue()).trim()
    assert.ok(profileSubmissionId)
    const profilePackOwnerId = String(await page.locator("#userId").inputValue()).trim() || "webui-user"
    assert.ok(profilePackOwnerId)
    const deniedProfilePackOwnerId = profilePackOwnerId === "u1" ? "u2" : "u1"
    const ownProfilePackDownloadStatus = await page.evaluate(async ({ sid, userId }) => {
      const response = await fetch(
        `/api/member/profile-pack/submissions/export/download?user_id=${encodeURIComponent(String(userId || ""))}&submission_id=${encodeURIComponent(String(sid || ""))}`,
      )
      return response.status
    }, { sid: profileSubmissionId, userId: profilePackOwnerId })
    assert.equal(ownProfilePackDownloadStatus, 200)
    const deniedProfilePackDownloadStatus = await page.evaluate(async ({ sid, userId }) => {
      const response = await fetch(
        `/api/member/profile-pack/submissions/export/download?user_id=${encodeURIComponent(String(userId || ""))}&submission_id=${encodeURIComponent(String(sid || ""))}`,
      )
      return response.status
    }, { sid: profileSubmissionId, userId: deniedProfilePackOwnerId })
    assert.equal(deniedProfilePackDownloadStatus, 403)

    await page.fill("#profilePackSubmissionPackFilter", "profile/research")
    const profileSubmissionListDelay = async (route) => {
      await delay(300)
      await route.continue()
    }
    await page.route(/\/api\/admin\/profile-pack\/submissions(?:\?.*)?$/, profileSubmissionListDelay)
    await page.click("#btnProfilePackListPackSubmissions")
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackSubmissionState")
      return node && !node.classList.contains("hidden") && /Loading Profile pack submissions/i.test(node.textContent || "")
    })
    await page.waitForFunction(() => {
      const rows = document.querySelectorAll("#profilePackSubmissionTable tbody tr")
      return rows.length > 0
    })
    await page.unroute(/\/api\/admin\/profile-pack\/submissions(?:\?.*)?$/, profileSubmissionListDelay)

    await page
      .locator("#profilePackSubmissionTable tbody tr")
      .first()
      .click()
    assert.equal(String(await page.locator("#profilePackDecisionSubmissionId").inputValue()).trim(), profileSubmissionId)

    await page.fill("#profilePackDecisionReviewLabels", "approved_with_notice")
    await page.fill("#profilePackDecisionReviewNote", "e2e approve profile/research")
    await page.click("#btnProfilePackDecideSubmission")
    await page.waitForFunction(() => {
      const rows = Array.from(document.querySelectorAll("#profilePackSubmissionTable tbody tr"))
      return rows.some((row) => /approved/i.test(String(row.textContent || "")))
    })

    await page.fill("#profilePackCatalogPackFilter", "profile/research")
    const profileCatalogDelay = async (route) => {
      await delay(300)
      await route.continue()
    }
    await page.route(/\/api\/profile-pack\/catalog(?:\?.*)?$/, profileCatalogDelay)
    await page.click("#btnProfilePackListCatalog")
    await page.waitForFunction(() => {
      const node = document.querySelector("#profilePackCatalogState")
      return node && !node.classList.contains("hidden") && /Loading Profile pack catalog/i.test(node.textContent || "")
    })
    await page.waitForFunction(() => {
      const rows = document.querySelectorAll("#profilePackCatalogTable tbody tr")
      return rows.length > 0
    })
    await page.unroute(/\/api\/profile-pack\/catalog(?:\?.*)?$/, profileCatalogDelay)

    await page
      .locator("#profilePackCatalogTable tbody tr")
      .first()
      .click()
    const selectedCatalogPackId = String(
      await page.locator("#profilePackCatalogPackId").inputValue(),
    ).trim()
    assert.ok(selectedCatalogPackId.length > 0)
    await page.click("#btnProfilePackCatalogDetail")
    await page.waitForFunction(() => {
      const summary = String(document.querySelector("#profilePackMarketSummary")?.textContent || "")
      if (!summary.trim()) return false
      if (/No profile pack market operation yet/i.test(summary)) return false
      return /status=/i.test(summary)
    })

    let insightsRequestCount = 0
    const insightsDelay = async (route) => {
      insightsRequestCount += 1
      await delay(300)
      await route.continue()
    }
    await page.route(/\/api\/profile-pack\/catalog\/insights(?:\?.*)?$/, insightsDelay)
    await page.goto(`${baseUrl}/market`, { waitUntil: "networkidle" })
    assert.equal(await page.locator("#marketUploadDropzone").isVisible(), true)
    await page.fill("#marketTemplateId", "community/basic")
    await page.selectOption("#marketInstallSourcePreference", "generated")
    await page.click("#btnMarketTemplateInstall")
    await page.waitForFunction(() => {
      const details = String(document.querySelector("#marketDetails")?.textContent || "")
      return (
        /"template_id":\s*"community\/basic"/.test(details) &&
        /"source":\s*"generated"/.test(details)
      )
    })
    await page.click("#btnMarketRefreshInstallations")
    await page.waitForFunction(() => {
      const rows = document.querySelectorAll("#marketInstallationsList .member-install-item")
      if (!rows.length) return false
      return /community\/basic/i.test(String(rows[0].textContent || ""))
    })
    await page.click("#btnMarketListSubmissions")
    await page.waitForFunction(() => {
      const state = document.querySelector("#marketSubmissionsState")
      const rows = document.querySelectorAll("#marketSubmissionsList .member-task-item")
      if (!state) return false
      if (/Failed to load/i.test(String(state.textContent || ""))) return false
      return rows.length >= 1
    })
    await page.locator("#marketSubmissionsList .member-task-item").first().click()
    await page.waitForFunction(() => {
      const details = String(document.querySelector("#marketDetails")?.textContent || "")
      return /"submission_id":\s*"/.test(details)
    })
    await page.click("#btnMarketListProfilePackSubmissions")
    await page.waitForFunction(() => {
      const state = document.querySelector("#marketProfilePackSubmissionsState")
      const rows = document.querySelectorAll("#marketProfilePackSubmissionsList .member-task-item")
      if (!state) return false
      if (/Failed to load/i.test(String(state.textContent || ""))) return false
      return rows.length >= 1
    })
    await page.locator("#marketProfilePackSubmissionsList .member-task-item").first().click()
    await page.click("#btnMarketDownloadProfilePackSubmission")
    await page.waitForFunction(() => {
      const details = String(document.querySelector("#marketDetails")?.textContent || "")
      return /"status":\s*"downloaded"/.test(details) && /"submission_id":\s*"/.test(details)
    })
    await page.waitForFunction(() => {
      const panel = document.querySelector("#marketDetailPanel")
      return Boolean(panel) && panel.open === false
    })
    await page.waitForFunction(() => {
      const facets = document.querySelectorAll('#marketFacetFilters input[type="checkbox"]')
      return facets.length >= 1
    })
    await page.waitForFunction(() => {
      const metrics = document.querySelectorAll("#marketCatalogMetrics .market-metric-card")
      return metrics.length >= 1
    })
    await page.waitForFunction(() => {
      const cards = document.querySelectorAll("#marketCatalogGrid .template-card")
      return cards.length >= 1
    })
    await page.waitForFunction(() => {
      const featuredState = String(document.querySelector("#marketFeaturedState")?.textContent || "")
      const trendingState = String(document.querySelector("#marketTrendingState")?.textContent || "")
      return /ready/i.test(featuredState) && /ready/i.test(trendingState)
    })
    const marketSnapshot = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll("#marketCatalogGrid .template-card"))
      const firstTitle = String(cards[0]?.querySelector(".template-card-title")?.textContent || "").trim()
      return {
        count: cards.length,
        firstTitle,
      }
    })
    assert.ok(marketSnapshot.count >= 1)
    assert.ok(marketSnapshot.firstTitle.length >= 1)
    await page.locator("#marketCatalogGrid .template-card").first().click()
    await page.waitForFunction(() => {
      const panel = document.querySelector("#marketDetailPanel")
      const packInput = document.querySelector("#marketPackId")
      return Boolean(panel) && panel.open === true && String(packInput?.value || "").trim().length > 0
    })

    await page.fill("#marketGlobalSearch", marketSnapshot.firstTitle)
    await page.waitForFunction(() => {
      const params = new URLSearchParams(location.search)
      return String(params.get("q") || "").trim().length > 0
    })
    await page.selectOption("#marketSortBy", "recent")
    await page.waitForFunction(() => {
      const params = new URLSearchParams(location.search)
      return String(params.get("sort") || "") === "recent"
    })
    const openFilterDrawerBtn = page.locator("#btnMarketOpenFilterDrawer")
    if (await openFilterDrawerBtn.count()) {
      await openFilterDrawerBtn.first().click()
      await page.waitForFunction(() => {
        const sidebar = document.querySelector("#marketFilterSidebar")
        if (!sidebar) return true
        const style = window.getComputedStyle(sidebar)
        if (style.display === "none" || style.visibility === "hidden") return false
        const rect = sidebar.getBoundingClientRect()
        return rect.right > 0
      })
    }
    const firstFacet = page.locator('#marketFacetFilters input[type="checkbox"]').first()
    if (await firstFacet.count()) {
      const facetGroup = await firstFacet.getAttribute("data-market-facet-group")
      await firstFacet.check()
      if (facetGroup) {
        await page.waitForFunction((group) => {
          const params = new URLSearchParams(location.search)
          return params.has(`facet_${group}`)
        }, facetGroup)
      }
    }
    assert.ok(insightsRequestCount >= 1)
    await page.unroute(/\/api\/profile-pack\/catalog\/insights(?:\?.*)?$/, insightsDelay)

    await page.goto(baseUrl, { waitUntil: "networkidle" })
    await page.selectOption("#role", "admin")
    await page.waitForFunction(() => {
      const node = document.querySelector("#btnListSubmissions")
      return Boolean(node) && !node.closest(".hidden")
    })

    await page.fill("#submissionStatus", "pending")

    const compareDelay = async (route) => {
      await delay(300)
      await route.continue()
    }
    const submissionDetailDelay = async (route) => {
      await delay(300)
      await route.continue()
    }
    const submissionsListDelay = async (route) => {
      await delay(300)
      await route.continue()
    }
    await page.route(/\/api\/admin\/submissions(?:\?.*)?$/, submissionsListDelay)
    await page.route("**/api/admin/submissions/detail**", submissionDetailDelay)
    await page.route("**/api/admin/submissions/compare**", compareDelay)

    await page.click("#btnListSubmissions")
    await page.waitForFunction(() => {
      const node = document.querySelector("#submissionListState")
      return node && !node.classList.contains("hidden") && /Loading Submissions/i.test(node.textContent || "")
    })
    await page.waitForSelector("tr[data-submission-id]")
    await page.waitForFunction(() => document.querySelector("#submissionListState")?.classList.contains("hidden"))

    const row = page.locator("tr[data-submission-id]").first()
    const submissionId = await row.getAttribute("data-submission-id")
    assert.ok(submissionId)
    const memberOwnerId = await page.evaluate(async (sid) => {
      const response = await fetch(
        `/api/admin/submissions/detail?role=admin&submission_id=${encodeURIComponent(String(sid || ""))}`,
      )
      if (!response.ok) return ""
      const payload = await response.json()
      return String(payload?.data?.data?.user_id || payload?.data?.user_id || "").trim()
    }, submissionId)
    assert.ok(memberOwnerId)
    const deniedMemberId = memberOwnerId === "u1" ? "u2" : "u1"
    const memberOwnDownloadStatus = await page.evaluate(async ({ sid, userId }) => {
      const response = await fetch(
        `/api/member/submissions/package/download?user_id=${encodeURIComponent(String(userId || ""))}&submission_id=${encodeURIComponent(String(sid || ""))}`,
      )
      return response.status
    }, { sid: submissionId, userId: memberOwnerId })
    assert.equal(memberOwnDownloadStatus, 200)
    const memberDeniedDownloadStatus = await page.evaluate(async ({ sid, userId }) => {
      const response = await fetch(
        `/api/member/submissions/package/download?user_id=${encodeURIComponent(String(userId || ""))}&submission_id=${encodeURIComponent(String(sid || ""))}`,
      )
      return response.status
    }, { sid: submissionId, userId: deniedMemberId })
    assert.equal(memberDeniedDownloadStatus, 403)

    await row.locator("td").first().click()

    await page.waitForFunction(() => {
      const node = document.querySelector("#submissionDetailState")
      return node && !node.classList.contains("hidden") && /Loading Submission detail/i.test(node.textContent || "")
    })
    await page.waitForFunction(() => {
      const node = document.querySelector("#compareState")
      return node && !node.classList.contains("hidden") && /Loading Submission compare/i.test(node.textContent || "")
    })
    await page.waitForFunction((id) => location.hash.includes("scope=submission") && location.hash.includes(id), submissionId)
    await page.waitForFunction((id) => {
      const node = document.querySelector("#submissionDetailSummary")
      return node && String(node.textContent || "").includes(id)
    }, submissionId)
    await page.waitForFunction(() => {
      const node = document.querySelector("#compareSummary")
      return node && /baseline_available/.test(node.textContent || "")
    })

    assert.match(await text(page, "#moderationSummary"), /community\/basic@1\.1\.0/)
    assert.match(await text(page, "#moderationWarnings"), /High-risk submission/i)
    assert.match(await text(page, "#moderationWarnings"), /ignore_previous_instructions/i)
    assert.match(await page.locator("#reviewLabels").inputValue(), /risk_high/)
    assert.match(await page.locator("#reviewNote").inputValue(), /Investigate warnings/)

    await page.click("#btnToggleDeveloperMode")
    await page.waitForFunction(() => /Developer mode:\s*on/i.test(String(document.querySelector("#developerModeLine")?.textContent || "")))
    await page.waitForFunction(() => document.querySelectorAll("#scanEvidenceList .scan-evidence-item").length > 0)

    await page.locator("#scanEvidenceList .scan-evidence-item").first().click()
    await page.waitForFunction(() => {
      const highlights = String(document.querySelector("#compareHighlights")?.textContent || "")
      const details = document.querySelector("#compareDetails")
      const compareRaw = details ? details.closest(".compare-raw") : null
      return (
        /evidence/i.test(highlights) &&
        Boolean(compareRaw && compareRaw.open)
      )
    })
    await page.waitForFunction(() => {
      const node = document.querySelector("#compareDetails")
      return node && node.classList.contains("is-focus-target")
    })

    await page.unroute(/\/api\/templates(?:\?.*)?$/, templatesListDelay)
    await page.unroute(/\/api\/admin\/submissions(?:\?.*)?$/, submissionsListDelay)
    await page.unroute("**/api/admin/submissions/detail**", submissionDetailDelay)
    await page.unroute("**/api/admin/submissions/compare**", compareDelay)
    await browser.close()
  } catch (error) {
    await page.screenshot({
      path: path.join(artifactDir, "sharelife-webui-e2e-failure.png"),
      fullPage: true,
    }).catch(() => {})
    await browser.close().catch(() => {})
    throw error
  }
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
