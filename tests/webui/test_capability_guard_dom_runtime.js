const test = require("node:test")
const assert = require("node:assert/strict")

const { applyCapabilityGuardToNode } = require("../../sharelife/webui/capability_guard_dom_runtime.js")

function makeNode() {
  const attributes = new Map()
  const classes = new Set()
  return {
    disabled: false,
    title: "",
    classList: {
      toggle(name, enabled) {
        if (enabled) {
          classes.add(name)
        } else {
          classes.delete(name)
        }
      },
      contains(name) {
        return classes.has(name)
      },
    },
    setAttribute(name, value) {
      attributes.set(name, String(value))
    },
    getAttribute(name) {
      return attributes.has(name) ? attributes.get(name) : null
    },
    removeAttribute(name) {
      attributes.delete(name)
    },
  }
}

test("applyCapabilityGuardToNode locks disallowed controls", () => {
  const node = makeNode()
  applyCapabilityGuardToNode(node, {
    allowed: false,
    lockedHint: "Requires capability: x.y.z",
  })
  assert.equal(node.classList.contains("capability-blocked"), true)
  assert.equal(node.getAttribute("aria-disabled"), "true")
  assert.equal(node.getAttribute("data-capability-locked"), "1")
  assert.equal(node.disabled, true)
  assert.equal(node.title, "Requires capability: x.y.z")
})

test("applyCapabilityGuardToNode unlocks previously locked controls", () => {
  const node = makeNode()
  applyCapabilityGuardToNode(node, {
    allowed: false,
    lockedHint: "Requires capability: x.y.z",
  })
  applyCapabilityGuardToNode(node, {
    allowed: true,
    lockedHint: "",
  })
  assert.equal(node.classList.contains("capability-blocked"), false)
  assert.equal(node.getAttribute("aria-disabled"), "false")
  assert.equal(node.getAttribute("data-capability-locked"), null)
  assert.equal(node.disabled, false)
  assert.equal(node.getAttribute("title"), null)
})

test("applyCapabilityGuardToNode tolerates null node", () => {
  assert.doesNotThrow(() => {
    applyCapabilityGuardToNode(null, { allowed: true })
  })
})
