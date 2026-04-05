(function bootstrapUiEventBus(globalScope) {
  const TOPICS = {
    UI_LOCALE_CHANGED: "ui.locale.changed",
    DEVELOPER_MODE_CHANGED: "ui.developer_mode.changed",
  }

  function normalizeTopic(topic) {
    return String(topic || "").trim()
  }

  function clonePayload(payload) {
    if (!payload || typeof payload !== "object") {
      return payload
    }
    return { ...payload }
  }

  function createEventBus() {
    const listeners = new Map()

    function listenerSet(topic, options = {}) {
      const normalized = normalizeTopic(topic)
      if (!normalized) {
        return null
      }
      if (!listeners.has(normalized) && options.create) {
        listeners.set(normalized, new Set())
      }
      return listeners.get(normalized) || null
    }

    function on(topic, handler) {
      if (typeof handler !== "function") {
        return () => {}
      }
      const bucket = listenerSet(topic, { create: true })
      if (!bucket) return () => {}
      bucket.add(handler)
      return () => off(topic, handler)
    }

    function off(topic, handler) {
      const bucket = listenerSet(topic)
      if (!bucket) return false
      const removed = bucket.delete(handler)
      if (!bucket.size) {
        listeners.delete(normalizeTopic(topic))
      }
      return removed
    }

    function once(topic, handler) {
      if (typeof handler !== "function") {
        return () => {}
      }
      const wrapped = (payload) => {
        off(topic, wrapped)
        handler(payload)
      }
      return on(topic, wrapped)
    }

    function emit(topic, payload) {
      const bucket = listenerSet(topic)
      if (!bucket || !bucket.size) return 0
      const snapshot = Array.from(bucket)
      const event = clonePayload(payload)
      snapshot.forEach((listener) => {
        listener(event)
      })
      return snapshot.length
    }

    function listenerCount(topic) {
      const bucket = listenerSet(topic)
      return bucket ? bucket.size : 0
    }

    function clear(topic) {
      const normalized = normalizeTopic(topic)
      if (normalized) {
        listeners.delete(normalized)
        return
      }
      listeners.clear()
    }

    return {
      TOPICS,
      on,
      off,
      once,
      emit,
      listenerCount,
      clear,
    }
  }

  const api = createEventBus()

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      TOPICS,
      createEventBus,
      bus: api,
    }
  }

  globalScope.SharelifeUiEventBus = api
})(typeof globalThis !== "undefined" ? globalThis : this)
