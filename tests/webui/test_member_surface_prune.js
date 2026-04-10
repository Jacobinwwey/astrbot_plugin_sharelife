const test = require("node:test")
const assert = require("node:assert/strict")

const {
  sectionIds,
  consoleLinkIds,
  removeNodesByIds,
  enforceMemberOnlySelect,
} = require("../../sharelife/webui/member_surface_prune.js")

test("sectionIds returns stable optional section list", () => {
  assert.deepEqual(sectionIds(), [
    "section-preferences",
    "section-risk-glossary",
    "section-reliability",
    "section-storage-backup",
    "section-retry-queue",
  ])
})

test("consoleLinkIds returns stable privileged link list", () => {
  assert.deepEqual(consoleLinkIds(), [
    "reviewerConsoleLink",
    "adminConsoleLink",
    "fullConsoleLink",
  ])
})

test("removeNodesByIds removes existing nodes only", () => {
  const removed = []
  const map = new Map(
    ["a", "b"].map((id) => [
      id,
      {
        parentNode: {
          removeChild(node) {
            removed.push(node.__id)
          },
        },
        __id: id,
      },
    ]),
  )
  removeNodesByIds((id) => map.get(id) || null, ["a", "b", "missing"])
  assert.deepEqual(removed, ["a", "b"])
})

test("enforceMemberOnlySelect removes non-member options and locks select", () => {
  const removed = []
  const options = [
    { value: "member", remove() { removed.push("member") } },
    { value: "reviewer", remove() { removed.push("reviewer") } },
    { value: "admin", remove() { removed.push("admin") } },
  ]
  const selectNode = {
    options,
    value: "admin",
    disabled: false,
  }
  enforceMemberOnlySelect(selectNode)
  assert.deepEqual(removed, ["reviewer", "admin"])
  assert.equal(selectNode.value, "member")
  assert.equal(selectNode.disabled, true)
})
