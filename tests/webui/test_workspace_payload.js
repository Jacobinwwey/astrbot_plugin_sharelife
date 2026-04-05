const test = require("node:test")
const assert = require("node:assert/strict")

const {
  extractWorkspacePayload,
} = require("../../sharelife/webui/workspace_payload.js")

test("extractWorkspacePayload unwraps api envelopes produced by webui fetch responses", () => {
  assert.deepEqual(
    extractWorkspacePayload({
      status: 200,
      data: {
        ok: true,
        message: "template detail ready",
        data: {
          template_id: "community/basic",
          published_at: "2026-03-26T12:00:00+00:00",
        },
      },
    }),
    {
      template_id: "community/basic",
      published_at: "2026-03-26T12:00:00+00:00",
    },
  )
})

test("extractWorkspacePayload returns direct payload objects unchanged", () => {
  assert.deepEqual(
    extractWorkspacePayload({
      comparison: { status: "baseline_available" },
      details: { prompt: { changed: true } },
    }),
    {
      comparison: { status: "baseline_available" },
      details: { prompt: { changed: true } },
    },
  )
})

test("extractWorkspacePayload tolerates empty or malformed responses", () => {
  assert.deepEqual(extractWorkspacePayload(null), {})
  assert.deepEqual(extractWorkspacePayload({ status: 500, data: { ok: false, message: "boom" } }), {})
})
