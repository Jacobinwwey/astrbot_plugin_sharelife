(function bootstrapMemberSurfacePrune(globalScope) {
  const OPTIONAL_SECTION_IDS = Object.freeze([
    "section-preferences",
    "section-risk-glossary",
    "section-reliability",
    "section-storage-backup",
    "section-retry-queue",
  ])

  const CONSOLE_LINK_IDS = Object.freeze([
    "reviewerConsoleLink",
    "adminConsoleLink",
    "fullConsoleLink",
  ])

  function sectionIds() {
    return Array.from(OPTIONAL_SECTION_IDS)
  }

  function consoleLinkIds() {
    return Array.from(CONSOLE_LINK_IDS)
  }

  function removeNodesByIds(byId, ids) {
    const getter = typeof byId === "function" ? byId : () => null
    const list = Array.isArray(ids) ? ids : []
    list.forEach((id) => {
      const node = getter(id)
      if (!node || !node.parentNode) return
      node.parentNode.removeChild(node)
    })
  }

  function enforceMemberOnlySelect(selectNode) {
    if (!selectNode) return
    Array.from(selectNode.options || []).forEach((option) => {
      const value = String(option && option.value || "").trim().toLowerCase()
      if (value !== "member") {
        option.remove()
      }
    })
    selectNode.value = "member"
    selectNode.disabled = true
  }

  const api = {
    sectionIds,
    consoleLinkIds,
    removeNodesByIds,
    enforceMemberOnlySelect,
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api
  }
  globalScope.SharelifeMemberSurfacePrune = api
})(typeof globalThis !== "undefined" ? globalThis : this)
