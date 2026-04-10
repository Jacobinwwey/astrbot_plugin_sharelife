(function installSharelifeAppBindingSlices(globalScope) {
  "use strict"

  function bindSidebarNavigationControls(deps) {
    const documentNode = deps.document
    Array.from(documentNode.querySelectorAll(".sidebar-link")).forEach((node) => {
      node.addEventListener("click", () => {
        Array.from(documentNode.querySelectorAll(".sidebar-link")).forEach((link) => {
          link.classList.remove("is-active")
        })
        node.classList.add("is-active")
      })
    })
  }

  function bindAuthPanelControls(deps) {
    deps.bindClick("loginBtn", deps.login)
    deps.bindChange("authRole", deps.syncReviewerAuthFields)
    const openLoginButton = deps.byId("btnAuthOpenLoginPanel")
    if (!openLoginButton) return
    openLoginButton.addEventListener("click", () => {
      deps.state.authPromptRequested = true
      deps.updateAuthUi()
      const passwordNode = deps.byId("authPassword")
      if (passwordNode && typeof passwordNode.focus === "function") {
        passwordNode.focus()
      }
    })
  }

  function bindLocaleAndDeveloperControls(deps) {
    deps.bindChange("role", () => {
      deps.applyConsoleScope()
      void deps.refreshCapabilities({ updateScope: false })
    })
    deps.bindChange("uiLocale", () => {
      deps.applyUiLocale(deps.byId("uiLocale").value, {
        persist: true,
        refreshCollections: true,
      })
    })
    deps.localeQuickButtons().forEach((node) => {
      node.addEventListener("click", () => {
        const locale = String(node.getAttribute("data-locale-option") || "").trim()
        if (!locale) return
        deps.applyUiLocale(locale, { persist: true, refreshCollections: true })
      })
    })
    const developerToggle = deps.byId("btnToggleDeveloperMode")
    if (!developerToggle) return
    developerToggle.addEventListener("click", () => {
      deps.setDeveloperMode(!deps.state.developerMode, { persist: true })
    })
  }

  function bindWorkspaceRouteControls(deps) {
    deps.bindClick("btnReloadWorkspace", () => {
      void deps.syncWorkspaceFromHash()
    })
    deps.bindClick("btnClearWorkspace", deps.clearWorkspaceRoute)
  }

  function bindPreferenceControls(deps) {
    deps.bindClick("btnPrefGet", async () => {
      const a = deps.actor()
      deps.render("get_preferences", await deps.api(`/api/preferences${deps.queryString({ user_id: a.user_id })}`))
    })

    deps.bindClick("btnModeSet", async () => {
      const a = deps.actor()
      deps.render("set_mode", await deps.api("/api/preferences/mode", {
        method: "POST",
        body: { ...a, mode: deps.byId("modeValue").value }
      }))
    })

    deps.bindClick("btnObserveSet", async () => {
      const a = deps.actor()
      deps.render("set_observe", await deps.api("/api/preferences/observe", {
        method: "POST",
        body: { ...a, enabled: deps.byId("observeValue").value === "true" }
      }))
    })
  }

  function bindMemberMarketControls(deps) {
    const listTemplatesButton = deps.byId("btnTemplates")
    if (listTemplatesButton) {
      listTemplatesButton.addEventListener("click", deps.listTemplates)
    }
    const memberSearchNode = deps.byId("memberGlobalSearch")
    if (memberSearchNode) {
      memberSearchNode.addEventListener("input", () => {
        const value = String(memberSearchNode.value || "").trim()
        const packQuery = deps.memberSpotlightProfilePackQuery(value)
        deps.state.memberPanel.searchQuery = value
        deps.renderMemberInstallations(deps.state.memberPanel.installations)
        deps.renderMemberImportDrafts(deps.state.memberPanel.importDrafts)
        const templateFilter = deps.byId("templateFilterId")
        const categoryFilter = deps.byId("templateCategoryFilter")
        if (templateFilter) {
          templateFilter.value = packQuery ? "" : value
        }
        if (value && deps.byId("trialTemplateId")) {
          deps.byId("trialTemplateId").value = value
        }
        if (value && categoryFilter) {
          categoryFilter.value = ""
          deps.setActiveMarketChip("")
        }
        deps.syncMemberSpotlightMarketJump(packQuery)
        if (packQuery) return
        deps.revealInlineMemberMarket()
        if (templateFilter && categoryFilter) {
          void deps.listTemplates()
        }
      })
      memberSearchNode.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") return
        event.preventDefault()
        const value = String(memberSearchNode.value || "").trim()
        const packQuery = deps.memberSpotlightProfilePackQuery(value)
        if (packQuery) {
          deps.openMemberSpotlightMarketQuery(packQuery)
          return
        }
        deps.revealInlineMemberMarket()
        if (deps.byId("templateFilterId") && deps.byId("templateCategoryFilter")) {
          void deps.listTemplates()
        }
      })
    }
    const memberSpotlightMarketJump = deps.byId("memberSpotlightMarketJump")
    if (memberSpotlightMarketJump) {
      memberSpotlightMarketJump.addEventListener("click", () => {
        deps.openMemberSpotlightMarketQuery(
          String(memberSpotlightMarketJump.dataset.marketQuery || "").trim(),
        )
      })
    }
    deps.marketChipButtons().forEach((node) => {
      node.addEventListener("click", () => {
        deps.revealInlineMemberMarket()
        const value = String(node.getAttribute("data-market-chip") || "").trim()
        const categoryFilter = deps.byId("templateCategoryFilter")
        if (categoryFilter) {
          categoryFilter.value = value
        }
        const memberSearch = deps.byId("memberGlobalSearch")
        if (memberSearch) {
          memberSearch.value = ""
        }
        deps.setActiveMarketChip(value)
        void deps.listTemplates()
      })
    })
  }

  function bindTemplateDrawerAndWizardControls(deps) {
    deps.bindClick("btnTemplateDrawerClose", deps.closeTemplateDrawer)
    deps.bindClick("btnDrawerTrial", () => {
      if (deps.state.marketHub.selectedTemplateId) {
        deps.byId("trialTemplateId").value = deps.state.marketHub.selectedTemplateId
      }
      deps.triggerControl("btnTrial")
    })
    deps.bindClick("btnDrawerInstall", () => {
      if (deps.state.marketHub.selectedTemplateId) {
        deps.byId("trialTemplateId").value = deps.state.marketHub.selectedTemplateId
      }
      deps.triggerControl("btnInstall")
    })
    deps.bindClick("btnDrawerPrompt", () => {
      if (deps.state.marketHub.selectedTemplateId) {
        deps.byId("trialTemplateId").value = deps.state.marketHub.selectedTemplateId
      }
      deps.triggerControl("btnPrompt")
    })
    deps.bindClick("btnDrawerPackage", () => {
      if (deps.state.marketHub.selectedTemplateId) {
        deps.byId("trialTemplateId").value = deps.state.marketHub.selectedTemplateId
      }
      deps.triggerControl("btnPackage")
    })
    deps.bindClick("btnDrawerDetail", () => {
      if (deps.state.marketHub.selectedTemplateId) {
        deps.byId("trialTemplateId").value = deps.state.marketHub.selectedTemplateId
      }
      deps.triggerControl("btnTemplateDetail")
    })
    deps.bindClick("btnOpenSubmitWizard", deps.openSubmitWizard)
    deps.bindClick("btnCloseSubmitWizard", deps.closeSubmitWizard)
    deps.bindClick("submitWizardBackdrop", deps.closeSubmitWizard)
    deps.bindClick("btnSubmitWizardPrev", () => {
      deps.setWizardStep(deps.state.marketHub.wizardStep - 1)
    })
    deps.bindClick("btnSubmitWizardNext", () => {
      if (deps.state.marketHub.wizardStep === 1 && !String(deps.byId("wizardTemplateId").value || "").trim()) {
        deps.byId("wizardTemplateId").focus()
        return
      }
      deps.setWizardStep(deps.state.marketHub.wizardStep + 1)
    })
    deps.bindClick("btnSubmitWizardPublish", () => {
      void deps.submitTemplateFromWizard()
    })
  }

  function bindTemplateExecutionControls(deps) {
    deps.bindClick("btnSubmitTemplate", async () => {
      const a = deps.actor()
      let packagePayload = {}
      try {
        packagePayload = await deps.selectedPackagePayload()
      } catch (error) {
        deps.render("submit_template", deps.uploadTooLargeResponse())
        return
      }
      deps.render("submit_template", await deps.api("/api/templates/submit", {
        method: "POST",
        body: {
          ...a,
          template_id: deps.byId("submitTemplateId").value,
          version: deps.byId("submitVersion").value || "1.0.0",
          upload_options: deps.readUploadOptionsFromForm(),
          ...packagePayload
        }
      }))
    })

    deps.bindClick("btnTrial", async () => {
      const a = deps.actor()
      const response = await deps.api("/api/trial", {
        method: "POST",
        body: {
          ...a,
          template_id: deps.byId("trialTemplateId").value
        }
      })
      deps.render("trial", response)
      if (!deps.workspaceRequestFailed(response)) {
        await deps.loadTrialStatus()
      }
    })

    deps.bindClick("btnTrialStatus", () => {
      void deps.loadTrialStatus()
    })

    deps.bindClick("btnInstall", async () => {
      const a = deps.actor()
      deps.render("install", await deps.api("/api/templates/install", {
        method: "POST",
        body: {
          ...a,
          template_id: deps.byId("trialTemplateId").value,
          install_options: deps.readInstallOptionsFromForm(),
        }
      }))
    })

    deps.bindClick("btnPrompt", async () => {
      deps.render("prompt", await deps.api("/api/templates/prompt", {
        method: "POST",
        body: { template_id: deps.byId("trialTemplateId").value }
      }))
    })

    deps.bindClick("btnPackage", async () => {
      deps.render("package", await deps.api("/api/templates/package", {
        method: "POST",
        body: { template_id: deps.byId("trialTemplateId").value }
      }))
    })

    deps.bindClick("btnTemplateDetail", deps.loadTemplateDetail)
    deps.bindClick("btnPackageDownload", deps.downloadPackage)
  }

  function bindProfilePackControls(deps) {
    deps.bindClick("btnDryrunPlan", () => {
      void deps.prepareDryrunPlan()
    })
    deps.bindClick("btnApplyPlan", () => {
      void deps.applyPlan()
    })
    deps.bindClick("btnRollbackPlan", () => {
      void deps.rollbackPlan()
    })
    deps.bindClick("btnProfilePackExport", () => {
      void deps.exportProfilePack()
    })
    deps.bindClick("btnProfilePackDownloadExport", () => {
      void deps.downloadProfilePackExport()
    })
    deps.bindClick("btnProfilePackListExports", () => {
      void deps.listProfilePackExports()
    })
    deps.bindClick("btnProfilePackImport", () => {
      void deps.importProfilePack()
    })
    deps.bindClick("btnProfilePackImportFromExport", () => {
      void deps.importProfilePackFromExport()
    })
    deps.bindClick("btnProfilePackImportDryrun", () => {
      void deps.importAndDryrunProfilePack()
    })
    deps.bindClick("btnProfilePackListImports", () => {
      void deps.listProfilePackImports()
    })
    deps.bindClick("btnProfilePackDryrun", () => {
      void deps.dryrunProfilePack()
    })
    deps.bindClick("btnProfilePackApply", () => {
      void deps.applyProfilePackPlan()
    })
    deps.bindClick("btnProfilePackRollback", () => {
      void deps.rollbackProfilePackPlan()
    })
    deps.bindClick("btnProfilePackPluginPlan", () => {
      void deps.loadProfilePackPluginInstallPlan()
    })
    deps.bindClick("btnProfilePackPluginConfirm", () => {
      void deps.confirmProfilePackPluginInstall()
    })
    deps.bindClick("btnProfilePackPluginExecute", () => {
      void deps.executeProfilePackPluginInstall()
    })
    deps.bindInput("profilePackRecordPackFilter", () => {
      deps.setProfilePackRecordPackFilter(deps.readProfilePackRecordPackFilter())
      deps.renderProfilePackRecords()
    })
    deps.bindClick("btnProfilePackClearRecordFilter", () => {
      deps.setProfilePackRecordPackFilter("")
      deps.renderProfilePackRecords()
    })
    deps.bindClick("btnProfilePackSubmitCommunity", () => {
      void deps.submitProfilePackToCommunity()
    })
    deps.bindClick("btnProfilePackListPackSubmissions", () => {
      void deps.listProfilePackMarketSubmissions()
    })
    deps.bindClick("btnProfilePackDecideSubmission", () => {
      void deps.decideProfilePackSubmission()
    })
    deps.bindClick("btnProfilePackListCatalog", () => {
      void deps.listProfilePackCatalog()
    })
    deps.bindClick("btnProfilePackCatalogDetail", () => {
      void deps.loadProfilePackCatalogDetail()
    })
    deps.bindClick("btnProfilePackCatalogCompare", () => {
      void deps.compareProfilePackCatalog()
    })
    deps.bindClick("btnProfilePackSetFeatured", () => {
      void deps.setProfilePackFeatured()
    })
  }

  function bindSubmissionReviewControls(deps) {
    deps.bindClick("btnListSubmissions", deps.listSubmissions)

    deps.bindClick("btnSaveSubmissionReview", deps.saveSubmissionReview)
    deps.bindClick("btnApproveSubmission", async () => {
      await deps.decideSubmission("approve")
    })
    deps.bindClick("btnRejectSubmission", async () => {
      await deps.decideSubmission("reject")
    })

    deps.bindClick("btnSubmissionDetail", deps.loadSubmissionDetail)
    deps.bindClick("btnCompareSubmission", deps.loadSubmissionCompare)
    deps.bindClick("btnDownloadSubmissionPackage", deps.downloadSubmissionPackage)
  }

  function bindAdminOperationsControls(deps) {
    deps.bindClick("btnListRetry", async () => {
      const a = deps.actor()
      deps.render("admin_list_retry", await deps.api(`/api/admin/retry-requests${deps.queryString({ role: a.role })}`))
    })

    deps.bindClick("btnLockRetry", async () => {
      const a = deps.actor()
      deps.render("admin_retry_lock", await deps.api("/api/admin/retry-requests/lock", {
        method: "POST",
        body: {
          ...a,
          request_id: deps.byId("lockRequestId").value,
          force: deps.byId("lockForce").checked,
          reason: deps.byId("lockReason").value
        }
      }))
    })

    deps.bindClick("btnRetryDecide", async () => {
      const a = deps.actor()
      deps.render("admin_retry_decide", await deps.api("/api/admin/retry-requests/decide", {
        method: "POST",
        body: {
          ...a,
          request_id: deps.byId("retryRequestId").value,
          decision: deps.byId("retryDecision").value,
          request_version: Number(deps.byId("retryRequestVersion").value || 0),
          lock_version: Number(deps.byId("retryLockVersion").value || 0)
        }
      }))
    })

    deps.bindClick("btnAudit", async () => {
      const a = deps.actor()
      const auditParams = {
        role: a.role,
        limit: deps.readIntegerField("auditLimit", 20, 1),
        lifecycle_only: deps.readCheckboxField("auditLifecycleOnly", false),
        reviewer_id: deps.readTextField("auditReviewerId", ""),
        device_id: deps.readTextField("auditDeviceId", ""),
        action_prefix: deps.readTextField("auditActionPrefix", ""),
        inspect_limit: deps.readIntegerField("auditInspectLimit", 1000, 1),
      }
      const response = await deps.api(`/api/admin/audit${deps.queryString({
        ...auditParams,
      })}`)
      deps.render("admin_audit", response)
      const data = deps.apiData(response)
      deps.setAuditOutput("auditSummaryOutput", deps.buildAuditSummaryText(data), data && data.summary ? data.summary : data)
      deps.setAuditOutput("auditEventsOutput", deps.buildAuditEventsText(data), data && data.events ? data.events : data)
    })

    deps.bindClick("btnNotice", async () => {
      deps.render("notifications", await deps.api(`/api/notifications${deps.queryString({
        limit: Number(deps.byId("noticeLimit").value || 50)
      })}`))
    })

    deps.bindClick("btnStorageSummary", async () => {
      const a = deps.actor()
      const response = await deps.api(`/api/admin/storage/local-summary${deps.queryString({ role: a.role })}`)
      deps.render("admin_storage_local_summary", response)
      const data = deps.apiData(response)
      deps.setStorageOutput("storageSummaryOutput", deps.buildStorageLocalSummaryText(data), data)
    })

    deps.bindClick("btnContinuityList", () => {
      void deps.listContinuityEntries()
    })

    deps.bindClick("btnContinuityGet", () => {
      void deps.getContinuityDetail()
    })

    deps.bindClick("btnStoragePoliciesGet", async () => {
      const a = deps.actor()
      const response = await deps.api(`/api/admin/storage/policies${deps.queryString({ role: a.role })}`)
      deps.render("admin_storage_get_policies", response)
      const data = deps.apiData(response)
      if (data && typeof data === "object" && data.policies && typeof data.policies === "object") {
        deps.applyStoragePolicyFields(data.policies)
      }
      deps.setStorageOutput("storagePoliciesOutput", deps.buildStoragePoliciesText(data), data)
    })

    deps.bindClick("btnStoragePoliciesSet", async () => {
      const a = deps.actor()
      const response = await deps.api("/api/admin/storage/policies", {
        method: "POST",
        body: {
          ...a,
          policy_patch: deps.readStoragePoliciesPatch(),
        },
      })
      deps.render("admin_storage_set_policies", response)
      const data = deps.apiData(response)
      if (data && typeof data === "object" && data.policies && typeof data.policies === "object") {
        deps.applyStoragePolicyFields(data.policies)
      }
      deps.setStorageOutput("storagePoliciesOutput", deps.buildStoragePoliciesText(data), data)
    })

    deps.bindClick("btnStorageRunBackup", async () => {
      const a = deps.actor()
      const response = await deps.api("/api/admin/storage/jobs/run", {
        method: "POST",
        body: {
          ...a,
          trigger: deps.readTextField("storageJobTrigger", "manual") || "manual",
          note: deps.readTextField("storageJobNote", ""),
        },
      })
      deps.render("admin_storage_run_job", response)
      const data = deps.apiData(response)
      const job = data && typeof data === "object" && data.job && typeof data.job === "object"
        ? data.job
        : null
      if (job) {
        deps.applyFieldPatches({
          storageJobId: job.job_id,
          storageRestoreArtifactRef: job.artifact_id || job.job_id || "",
        })
      }
      deps.setStorageOutput("storageJobsOutput", deps.buildStorageJobDetailText(data), data)
    })

    deps.bindClick("btnStorageJobsList", async () => {
      const a = deps.actor()
      const status = deps.readTextField("storageJobsStatus", "")
      const limit = deps.readIntegerField("storageJobsLimit", 20, 1)
      const response = await deps.api(`/api/admin/storage/jobs${deps.queryString({ role: a.role, status, limit })}`)
      deps.render("admin_storage_list_jobs", response)
      const data = deps.apiData(response)
      deps.setStorageOutput("storageJobsOutput", deps.buildStorageJobsText(data), data)
    })

    deps.bindClick("btnStorageJobGet", async () => {
      const a = deps.actor()
      const jobId = deps.readTextField("storageJobId", "")
      if (!jobId) {
        deps.setStorageOutput(
          "storageJobsOutput",
          deps.i18nMessage("storage.output.job_id_required", "job_id is required."),
          { error: "job_id_required" },
        )
        return
      }
      const response = await deps.api(`/api/admin/storage/jobs/${encodeURIComponent(jobId)}${deps.queryString({ role: a.role })}`)
      deps.render("admin_storage_get_job", response)
      const data = deps.apiData(response)
      const job = data && typeof data === "object" && data.job && typeof data.job === "object"
        ? data.job
        : null
      if (job) {
        deps.applyFieldPatches({
          storageRestoreArtifactRef: job.artifact_id || job.job_id || "",
        })
      }
      deps.setStorageOutput("storageJobsOutput", deps.buildStorageJobDetailText(data), data)
    })

    deps.bindClick("btnStorageRestorePrepare", async () => {
      const a = deps.actor()
      const artifactRef = deps.readTextField("storageRestoreArtifactRef", "")
      if (!artifactRef) {
        deps.setStorageOutput(
          "storageRestoreOutput",
          deps.i18nMessage("storage.output.artifact_ref_required", "artifact_ref is required."),
          { error: "artifact_ref_required" },
        )
        return
      }
      const response = await deps.api("/api/admin/storage/restore/prepare", {
        method: "POST",
        body: {
          ...a,
          artifact_ref: artifactRef,
          note: deps.readTextField("storageRestoreNote", ""),
        },
      })
      deps.render("admin_storage_restore_prepare", response)
      const data = deps.apiData(response)
      const restore = data && typeof data === "object" && data.restore && typeof data.restore === "object"
        ? data.restore
        : null
      if (restore) {
        deps.applyFieldPatches({
          storageRestoreId: restore.restore_id,
          storageRestoreJobId: restore.restore_id,
        })
      }
      deps.setStorageOutput("storageRestoreOutput", deps.buildStorageRestoreText(data), data)
    })

    deps.bindClick("btnStorageRestoreCommit", async () => {
      const a = deps.actor()
      const restoreId = deps.readTextField("storageRestoreId", "")
      if (!restoreId) {
        deps.setStorageOutput(
          "storageRestoreOutput",
          deps.i18nMessage("storage.output.restore_id_required", "restore_id is required."),
          { error: "restore_id_required" },
        )
        return
      }
      const response = await deps.api("/api/admin/storage/restore/commit", {
        method: "POST",
        body: {
          ...a,
          restore_id: restoreId,
        },
      })
      deps.render("admin_storage_restore_commit", response)
      const data = deps.apiData(response)
      deps.setStorageOutput("storageRestoreOutput", deps.buildStorageRestoreText(data), data)
    })

    deps.bindClick("btnStorageRestoreCancel", async () => {
      const a = deps.actor()
      const restoreId = deps.readTextField("storageRestoreId", "")
      if (!restoreId) {
        deps.setStorageOutput(
          "storageRestoreOutput",
          deps.i18nMessage("storage.output.restore_id_required", "restore_id is required."),
          { error: "restore_id_required" },
        )
        return
      }
      const response = await deps.api("/api/admin/storage/restore/cancel", {
        method: "POST",
        body: {
          ...a,
          restore_id: restoreId,
        },
      })
      deps.render("admin_storage_restore_cancel", response)
      const data = deps.apiData(response)
      deps.setStorageOutput("storageRestoreOutput", deps.buildStorageRestoreText(data), data)
    })

    deps.bindClick("btnStorageRestoreJobsList", async () => {
      const a = deps.actor()
      const stateFilter = deps.readTextField("storageRestoreJobsState", "")
      const limit = deps.readIntegerField("storageRestoreJobsLimit", 20, 1)
      const response = await deps.api(`/api/admin/storage/restore/jobs${deps.queryString({ role: a.role, state: stateFilter, limit })}`)
      deps.render("admin_storage_list_restore_jobs", response)
      const data = deps.apiData(response)
      deps.setStorageOutput("storageRestoreJobsOutput", deps.buildStorageRestoreJobsText(data), data)
    })

    deps.bindClick("btnStorageRestoreJobGet", async () => {
      const a = deps.actor()
      const restoreId = deps.readTextField("storageRestoreJobId", "")
      if (!restoreId) {
        deps.setStorageOutput(
          "storageRestoreJobsOutput",
          deps.i18nMessage("storage.output.restore_id_required", "restore_id is required."),
          { error: "restore_id_required" },
        )
        return
      }
      const response = await deps.api(`/api/admin/storage/restore/jobs/${encodeURIComponent(restoreId)}${deps.queryString({ role: a.role })}`)
      deps.render("admin_storage_get_restore_job", response)
      const data = deps.apiData(response)
      const restore = data && typeof data === "object" && data.restore && typeof data.restore === "object"
        ? data.restore
        : null
      if (restore) {
        deps.applyFieldPatches({ storageRestoreId: restore.restore_id })
      }
      deps.setStorageOutput("storageRestoreJobsOutput", deps.buildStorageRestoreText(data), data)
    })
  }

  function bindMemberImportControls(deps) {
    const importAstrbotButton = deps.byId("btnImportAstrbotConfig")
    if (importAstrbotButton) {
      importAstrbotButton.addEventListener("click", () => {
        void deps.importMemberLocalAstrbotConfig()
      })
    }
    const importConfigPackButton = deps.byId("btnImportConfigPackFile")
    if (importConfigPackButton) {
      importConfigPackButton.addEventListener("click", () => {
        deps.promptMemberProfilePackImport()
      })
    }
    const openMemberImportReviewButton = deps.byId("btnOpenMemberImportReview")
    if (openMemberImportReviewButton) {
      openMemberImportReviewButton.addEventListener("click", () => {
        deps.openMemberProfilePackUploadModalById("")
      })
    }
    const importAstrbotInput = deps.byId("memberImportAstrbotConfigFile")
    if (importAstrbotInput) {
      importAstrbotInput.addEventListener("change", () => {
        void deps.importMemberProfilePackFromSelection()
      })
    }
    const refreshMemberInstallationsButton = deps.byId("btnRefreshMemberInstallationsInline")
    if (refreshMemberInstallationsButton) {
      refreshMemberInstallationsButton.addEventListener("click", () => {
        void deps.loadMemberInstallations({ refresh: true })
      })
    }
    const memberProfilePackUploadClose = deps.byId("btnCloseMemberProfilePackUploadModal")
    if (memberProfilePackUploadClose) {
      memberProfilePackUploadClose.addEventListener("click", deps.closeMemberProfilePackUploadModal)
    }
    const memberProfilePackUploadCancel = deps.byId("btnMemberProfilePackUploadCancel")
    if (memberProfilePackUploadCancel) {
      memberProfilePackUploadCancel.addEventListener("click", deps.closeMemberProfilePackUploadModal)
    }
    const memberProfilePackUploadBackdrop = deps.byId("memberProfilePackUploadBackdrop")
    if (memberProfilePackUploadBackdrop) {
      memberProfilePackUploadBackdrop.addEventListener("click", deps.closeMemberProfilePackUploadModal)
    }
    const memberProfilePackUploadSubmit = deps.byId("btnMemberProfilePackUploadSubmit")
    if (memberProfilePackUploadSubmit) {
      memberProfilePackUploadSubmit.addEventListener("click", () => {
        void deps.submitSelectedMemberImportDraft()
      })
    }
    const memberProfilePackUploadDelete = deps.byId("btnMemberProfilePackUploadDelete")
    if (memberProfilePackUploadDelete) {
      memberProfilePackUploadDelete.addEventListener("click", () => {
        void deps.deleteMemberImportDraft()
      })
    }
    deps.bindUploadDropZone({
      zoneId: "memberUploadDropzone",
      inputId: "memberImportAstrbotConfigFile",
      outputId: "memberUploadFileName",
      emptyKey: "member.upload.file_idle",
      emptyFallback: "No file selected. Max 20 MiB. Sharelife standard zip, AstrBot backup zip, cmd_config.json, and abconf_*.json are supported.",
    })
  }

  function bindReviewerLifecycleControls(deps) {
    const reviewerInviteCreateButton = deps.byId("btnReviewerInviteCreate")
    if (reviewerInviteCreateButton) {
      reviewerInviteCreateButton.addEventListener("click", () => {
        void deps.createReviewerInvite()
      })
    }
    const reviewerInviteListButton = deps.byId("btnReviewerInviteList")
    if (reviewerInviteListButton) {
      reviewerInviteListButton.addEventListener("click", () => {
        void deps.listReviewerInvites()
      })
    }
    const reviewerAccountListButton = deps.byId("btnReviewerAccountList")
    if (reviewerAccountListButton) {
      reviewerAccountListButton.addEventListener("click", () => {
        void deps.listReviewerAccounts()
      })
    }
    const reviewerDeviceListButton = deps.byId("btnReviewerDeviceList")
    if (reviewerDeviceListButton) {
      reviewerDeviceListButton.addEventListener("click", () => {
        void deps.listReviewerDevices()
      })
    }
    const reviewerDeviceResetButton = deps.byId("btnReviewerDeviceReset")
    if (reviewerDeviceResetButton) {
      reviewerDeviceResetButton.addEventListener("click", () => {
        void deps.resetReviewerDevices()
      })
    }
    const reviewerSessionListButton = deps.byId("btnReviewerSessionList")
    if (reviewerSessionListButton) {
      reviewerSessionListButton.addEventListener("click", () => {
        void deps.listReviewerSessions()
      })
    }
    const reviewerSessionRevokeButton = deps.byId("btnReviewerSessionRevoke")
    if (reviewerSessionRevokeButton) {
      reviewerSessionRevokeButton.addEventListener("click", () => {
        void deps.revokeReviewerSessions()
      })
    }
    const reviewerDeviceTargetNode = deps.byId("reviewerDeviceTargetId")
    if (reviewerDeviceTargetNode) {
      reviewerDeviceTargetNode.addEventListener("change", () => {
        deps.setReviewerLifecycleSelectedReviewer(String(reviewerDeviceTargetNode.value || "").trim())
      })
    }
  }

  const existing = globalScope.SharelifeAppBindingSlices && typeof globalScope.SharelifeAppBindingSlices === "object"
    ? globalScope.SharelifeAppBindingSlices
    : {}
  globalScope.SharelifeAppBindingSlices = Object.assign(existing, {
    bindAdminOperationsControls,
    bindMemberImportControls,
    bindProfilePackControls,
    bindReviewerLifecycleControls,
    bindSubmissionReviewControls,
    bindSidebarNavigationControls,
    bindAuthPanelControls,
    bindLocaleAndDeveloperControls,
    bindWorkspaceRouteControls,
    bindPreferenceControls,
    bindMemberMarketControls,
    bindTemplateDrawerAndWizardControls,
    bindTemplateExecutionControls,
  })
})(typeof globalThis !== "undefined" ? globalThis : window)
