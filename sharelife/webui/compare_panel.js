(function bootstrapComparePanel(globalScope) {
  function textValue(value, fallback = "-") {
    if (value === undefined || value === null || value === "") {
      return fallback
    }
    if (typeof value === "boolean") {
      return String(value)
    }
    return String(value)
  }

  function listValue(items) {
    return Array.isArray(items) && items.length ? items.join(", ") : "-"
  }

  function lengthValue(size) {
    if (size === undefined || size === null) {
      return "-"
    }
    return `${size} chars`
  }

  function sizeValue(size) {
    if (size === undefined || size === null) {
      return "-"
    }
    return `${size} bytes`
  }

  function row(label, submission, published, changed, extra) {
    return {
      label,
      submission: textValue(submission),
      published: textValue(published),
      changed: Boolean(changed),
      tone: changed ? "danger" : "neutral",
      added: Array.isArray(extra && extra.added) ? extra.added : [],
      removed: Array.isArray(extra && extra.removed) ? extra.removed : [],
    }
  }

  function buildCompareViewModel(payload) {
    const data = payload || {}
    const comparison = data.comparison || {}
    const details = data.details || {}
    if (!data.comparison || !data.details) {
      return {
        empty: true,
        message: "No comparison loaded yet.",
        summary: {
          status: "unknown",
          versionChanged: false,
          riskChanged: false,
          hasSubmissionPackage: false,
          hasPublishedPackage: false,
        },
        highlights: [],
        sections: [],
      }
    }

    return {
      empty: false,
      message: "",
      summary: {
        status: textValue(comparison.status, "unknown"),
        versionChanged: Boolean(comparison.version_changed),
        riskChanged: Boolean(comparison.risk_level_changed),
        hasSubmissionPackage: Boolean(comparison.has_submission_package),
        hasPublishedPackage: Boolean(comparison.has_published_package),
      },
      highlights: [
        details.version && details.version.changed ? { label: "Version changed", tone: "danger" } : null,
        details.risk_level && details.risk_level.changed ? { label: "Risk changed", tone: "danger" } : null,
        details.prompt && details.prompt.changed ? { label: "Prompt changed", tone: "danger" } : null,
        details.review_labels && details.review_labels.changed ? { label: "Review labels changed", tone: "warning" } : null,
        details.warning_flags && details.warning_flags.changed ? { label: "Warning flags changed", tone: "warning" } : null,
        details.package && details.package.changed ? { label: "Package changed", tone: "warning" } : null,
        details.scan && details.scan.changed ? { label: "Scan changed", tone: "warning" } : null,
      ].filter(Boolean),
      sections: [
        {
          title: "Version and Risk",
          rows: [
            row(
              "Version",
              details.version && details.version.submission,
              details.version && details.version.published,
              details.version && details.version.changed,
            ),
            row(
              "Risk level",
              details.risk_level && details.risk_level.submission,
              details.risk_level && details.risk_level.published,
              details.risk_level && details.risk_level.changed,
            ),
            row(
              "Review note",
              details.review_note && details.review_note.submission,
              details.review_note && details.review_note.published,
              details.review_note && details.review_note.changed,
            ),
          ],
        },
        {
          title: "Prompt",
          rows: [
            row(
              "Preview",
              details.prompt && details.prompt.submission_preview,
              details.prompt && details.prompt.published_preview,
              details.prompt && details.prompt.changed,
            ),
            row(
              "Length",
              lengthValue(details.prompt && details.prompt.submission_length),
              lengthValue(details.prompt && details.prompt.published_length),
              details.prompt && details.prompt.changed,
            ),
          ],
        },
        {
          title: "Labels and Flags",
          rows: [
            row(
              "Review labels",
              listValue(details.review_labels && details.review_labels.submission),
              listValue(details.review_labels && details.review_labels.published),
              details.review_labels && details.review_labels.changed,
              details.review_labels,
            ),
            row(
              "Warning flags",
              listValue(details.warning_flags && details.warning_flags.submission),
              listValue(details.warning_flags && details.warning_flags.published),
              details.warning_flags && details.warning_flags.changed,
              details.warning_flags,
            ),
          ],
        },
        {
          title: "Package",
          rows: [
            row(
              "Filename",
              details.package && details.package.submission_filename,
              details.package && details.package.published_filename,
              details.package && details.package.filename_changed,
            ),
            row(
              "Checksum",
              details.package && details.package.submission_sha256,
              details.package && details.package.published_sha256,
              details.package && details.package.sha256_changed,
            ),
            row(
              "Size",
              sizeValue(details.package && details.package.submission_size_bytes),
              sizeValue(details.package && details.package.published_size_bytes),
              details.package && details.package.changed,
            ),
          ],
        },
        {
          title: "Scan",
          rows: [
            row(
              "Compatibility",
              details.scan && details.scan.submission_compatibility,
              details.scan && details.scan.published_compatibility,
              details.scan && details.scan.compatibility_changed,
            ),
            row(
              "Levels",
              listValue(details.scan && details.scan.submission_levels),
              listValue(details.scan && details.scan.published_levels),
              details.scan && details.scan.changed,
              {
                added: details.scan && details.scan.levels_added,
                removed: details.scan && details.scan.levels_removed,
              },
            ),
            row(
              "Prompt injection detected",
              details.scan && details.scan.submission_prompt_injection_detected,
              details.scan && details.scan.published_prompt_injection_detected,
              details.scan && details.scan.prompt_injection_detected_changed,
            ),
          ],
        },
      ],
    }
  }

  const api = { buildCompareViewModel }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeCompare = api
})(typeof globalThis !== "undefined" ? globalThis : this)
