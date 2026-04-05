(function bootstrapDetailPanel(globalScope) {
  const riskGlossaryItems = [
    {
      group: "Risk levels",
      groupKey: "risk_glossary.group.risk_levels",
      key: "low",
      title: "Low risk",
      titleKey: "risk_glossary.item.low.title",
      description: "Basic templates with no elevated orchestration or prompt-injection hits.",
      descriptionKey: "risk_glossary.item.low.description",
    },
    {
      group: "Risk levels",
      groupKey: "risk_glossary.group.risk_levels",
      key: "medium",
      title: "Medium risk",
      titleKey: "risk_glossary.item.medium.title",
      description: "Requires extra review because of compatibility gaps or level-L2 behavior.",
      descriptionKey: "risk_glossary.item.medium.description",
    },
    {
      group: "Risk levels",
      groupKey: "risk_glossary.group.risk_levels",
      key: "high",
      title: "High risk",
      titleKey: "risk_glossary.item.high.title",
      description: "Contains prompt-injection hits or level-L3 capability and should stay review-first.",
      descriptionKey: "risk_glossary.item.high.description",
    },
    {
      group: "Review labels",
      groupKey: "risk_glossary.group.review_labels",
      key: "prompt_injection_detected",
      title: "Prompt injection detected",
      titleKey: "risk_glossary.item.prompt_injection_detected.title",
      description: "The uploaded content matched one or more prompt-injection heuristics.",
      descriptionKey: "risk_glossary.item.prompt_injection_detected.description",
    },
    {
      group: "Review labels",
      groupKey: "risk_glossary.group.review_labels",
      key: "provider_override",
      title: "Provider override",
      titleKey: "risk_glossary.item.provider_override.title",
      description: "The template bundle carries provider-level overrides and needs admin validation.",
      descriptionKey: "risk_glossary.item.provider_override.description",
    },
    {
      group: "Review labels",
      groupKey: "risk_glossary.group.review_labels",
      key: "agent_orchestration",
      title: "Agent orchestration",
      titleKey: "risk_glossary.item.agent_orchestration.title",
      description: "The bundle declares sub-agent or agent orchestration capabilities.",
      descriptionKey: "risk_glossary.item.agent_orchestration.description",
    },
    {
      group: "Warning flags",
      groupKey: "risk_glossary.group.warning_flags",
      key: "ignore_previous_instructions",
      title: "Ignore previous instructions",
      titleKey: "risk_glossary.item.ignore_previous_instructions.title",
      description: "The prompt tries to override prior instructions.",
      descriptionKey: "risk_glossary.item.ignore_previous_instructions.description",
    },
    {
      group: "Warning flags",
      groupKey: "risk_glossary.group.warning_flags",
      key: "reveal_system_prompt",
      title: "Reveal system prompt",
      titleKey: "risk_glossary.item.reveal_system_prompt.title",
      description: "The prompt asks to expose protected system or developer instructions.",
      descriptionKey: "risk_glossary.item.reveal_system_prompt.description",
    },
  ]

  function textValue(value, fallback = "-") {
    if (value === undefined || value === null || value === "") {
      return fallback
    }
    return String(value)
  }

  function lengthValue(value) {
    if (value === undefined || value === null) {
      return "-"
    }
    return `${value} chars`
  }

  function numberValue(value) {
    if (value === undefined || value === null || value === "") {
      return "0"
    }
    return String(Number(value) || 0)
  }

  function listBadges(items) {
    return (Array.isArray(items) ? items : []).map((item) => ({ label: String(item) }))
  }

  function listValue(items) {
    return Array.isArray(items) && items.length ? items.join(", ") : "-"
  }

  function engagement(detail) {
    const raw = detail && detail.engagement && typeof detail.engagement === "object" ? detail.engagement : {}
    return {
      trial_requests: Number(raw.trial_requests || 0),
      installs: Number(raw.installs || 0),
      prompt_generations: Number(raw.prompt_generations || 0),
      package_generations: Number(raw.package_generations || 0),
      community_submissions: Number(raw.community_submissions || 0),
      last_activity_at: textValue(raw.last_activity_at, "-"),
    }
  }

  function buildTemplateSignalsSummary(detail) {
    const data = engagement(detail)
    return [
      `trial ${data.trial_requests}`,
      `install ${data.installs}`,
      `prompt ${data.prompt_generations}`,
      `pkg ${data.package_generations}`,
    ].join(" | ")
  }

  function buildTemplateDetailViewModel(detail) {
    const data = detail || {}
    if (!data.template_id) {
      return {
        empty: true,
        message: "No template detail loaded yet.",
        summary: "",
        badges: [],
        rows: [],
      }
    }
    return {
      empty: false,
      message: "",
      summary: `${textValue(data.template_id)}@${textValue(data.version)}`,
      badges: [
        { label: textValue(data.risk_level, "unknown") },
        ...listBadges(data.review_labels),
        ...listBadges(data.warning_flags),
      ],
      rows: [
        { label: "Source submission", value: textValue(data.source_submission_id) },
        { label: "Category", value: textValue(data.category) },
        { label: "Tags", value: listValue(data.tags) },
        { label: "Maintainer", value: textValue(data.maintainer) },
        { label: "Source channel", value: textValue(data.source_channel) },
        { label: "Trial requests", value: numberValue(engagement(data).trial_requests) },
        { label: "Installs", value: numberValue(engagement(data).installs) },
        { label: "Prompt generations", value: numberValue(engagement(data).prompt_generations) },
        { label: "Package generations", value: numberValue(engagement(data).package_generations) },
        { label: "Community submissions", value: numberValue(engagement(data).community_submissions) },
        { label: "Last activity", value: textValue(engagement(data).last_activity_at) },
        { label: "Published at", value: textValue(data.published_at) },
        { label: "Package", value: textValue(data.package_artifact && data.package_artifact.filename) },
        { label: "Prompt length", value: lengthValue(data.prompt_length) },
        { label: "Prompt preview", value: textValue(data.prompt_preview) },
        { label: "Review note", value: textValue(data.review_note) },
      ],
    }
  }

  function buildSubmissionDetailViewModel(detail) {
    const data = detail || {}
    if (!data.submission_id) {
      return {
        empty: true,
        message: "No submission detail loaded yet.",
        summary: "",
        badges: [],
        rows: [],
      }
    }
    return {
      empty: false,
      message: "",
      summary: textValue(data.submission_id),
      badges: [
        { label: textValue(data.status, "unknown") },
        { label: textValue(data.risk_level, "unknown") },
        ...listBadges(data.review_labels),
        ...listBadges(data.warning_flags),
      ],
      rows: [
        { label: "Template", value: textValue(data.template_id) },
        { label: "Version", value: textValue(data.version) },
        { label: "User", value: textValue(data.user_id) },
        { label: "Created at", value: textValue(data.created_at) },
        { label: "Updated at", value: textValue(data.updated_at) },
        { label: "Prompt length", value: lengthValue(data.prompt_length) },
        { label: "Prompt preview", value: textValue(data.prompt_preview) },
        { label: "Review note", value: textValue(data.review_note) },
        { label: "Package", value: textValue(data.package_artifact && data.package_artifact.filename) },
      ],
    }
  }

  const api = {
    riskGlossaryItems,
    buildTemplateDetailViewModel,
    buildSubmissionDetailViewModel,
    buildTemplateSignalsSummary,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeDetail = api
})(typeof globalThis !== "undefined" ? globalThis : this)
