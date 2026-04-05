from sharelife.application.services_registry import RegistryService
from sharelife.infrastructure.local_store import LocalStore


class FailingSource:
    def fetch_index(self):
        raise RuntimeError("network down")


class StaticSource:
    def __init__(self, payload):
        self.payload = payload

    def fetch_index(self):
        return self.payload


def test_registry_service_uses_cache_on_fetch_failure(tmp_path):
    store = LocalStore(tmp_path)
    store.save_json("registry/index.json", {"templates": [{"template_id": "a"}]})
    svc = RegistryService(source=FailingSource(), store=store)

    data = svc.refresh_or_load()

    assert data["templates"][0]["template_id"] == "a"


def test_registry_service_persists_latest_on_success(tmp_path):
    store = LocalStore(tmp_path)
    latest = {"templates": [{"template_id": "fresh"}]}
    svc = RegistryService(source=StaticSource(latest), store=store)

    data = svc.refresh_or_load()
    cached = store.load_json("registry/index.json", {})

    assert data == latest
    assert cached == latest
