const test = require("node:test")
const assert = require("node:assert/strict")

const { TOPICS, createEventBus, bus } = require("../../sharelife/webui/ui_event_bus.js")

test("event bus supports on/off/emit lifecycle", () => {
  const eventBus = createEventBus()
  let received = null
  const off = eventBus.on(TOPICS.UI_LOCALE_CHANGED, (payload) => {
    received = payload
  })
  assert.equal(eventBus.listenerCount(TOPICS.UI_LOCALE_CHANGED), 1)

  const count = eventBus.emit(TOPICS.UI_LOCALE_CHANGED, { locale: "ja-JP" })
  assert.equal(count, 1)
  assert.deepEqual(received, { locale: "ja-JP" })

  off()
  assert.equal(eventBus.listenerCount(TOPICS.UI_LOCALE_CHANGED), 0)
})

test("event bus once listener only runs once", () => {
  const eventBus = createEventBus()
  let hit = 0
  eventBus.once(TOPICS.DEVELOPER_MODE_CHANGED, () => {
    hit += 1
  })
  eventBus.emit(TOPICS.DEVELOPER_MODE_CHANGED, { enabled: true })
  eventBus.emit(TOPICS.DEVELOPER_MODE_CHANGED, { enabled: false })
  assert.equal(hit, 1)
  assert.equal(eventBus.listenerCount(TOPICS.DEVELOPER_MODE_CHANGED), 0)
})

test("event bus clear removes scoped and all listeners", () => {
  const eventBus = createEventBus()
  const noop = () => {}
  eventBus.on(TOPICS.UI_LOCALE_CHANGED, noop)
  eventBus.on(TOPICS.DEVELOPER_MODE_CHANGED, noop)
  assert.equal(eventBus.listenerCount(TOPICS.UI_LOCALE_CHANGED), 1)
  assert.equal(eventBus.listenerCount(TOPICS.DEVELOPER_MODE_CHANGED), 1)

  eventBus.clear(TOPICS.UI_LOCALE_CHANGED)
  assert.equal(eventBus.listenerCount(TOPICS.UI_LOCALE_CHANGED), 0)
  assert.equal(eventBus.listenerCount(TOPICS.DEVELOPER_MODE_CHANGED), 1)

  eventBus.clear()
  assert.equal(eventBus.listenerCount(TOPICS.DEVELOPER_MODE_CHANGED), 0)
})

test("shared global bus exposes topics and emit API", () => {
  assert.ok(bus)
  assert.equal(typeof bus.emit, "function")
  assert.equal(typeof bus.on, "function")
  assert.equal(TOPICS.UI_LOCALE_CHANGED, "ui.locale.changed")
})
