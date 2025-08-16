
import importlib.util
import sys
import pathlib
from typing import List, Dict, Tuple

import pytest
from fastapi.testclient import TestClient

BASE = pathlib.Path(__file__).resolve().parents[1] / 'src'

def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(f'harvester_module.{name}', BASE / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module

# Preload dependent modules for relative imports
_load_module('config')
models = _load_module('models')
_load_module('fetcher')
_load_module('storage')
RawTrendItem = models.RawTrendItem

main_spec = importlib.util.spec_from_file_location('harvester_module.main', BASE / 'main.py')
harvester_main = importlib.util.module_from_spec(main_spec)
harvester_main.__package__ = 'harvester_module'
main_spec.loader.exec_module(harvester_main)  # type: ignore
app = harvester_main.app


class DummyFetcher:
    async def run(self, limit: int = 5) -> Tuple[List[RawTrendItem], Dict[str, str]]:
        item = RawTrendItem(title='t1', source='dummy', keywords=['k'])
        return [item], {}


class DummyStorage:
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def save_items(self, items: List[RawTrendItem]) -> int:
        return len(items)


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(harvester_main, 'FetcherEngine', lambda: DummyFetcher())
    monkeypatch.setattr(harvester_main, 'StorageService', lambda *a, **k: DummyStorage())


def test_trigger_harvest_mock() -> None:
    client = TestClient(app)
    resp = client.post('/harvest/trigger')
    assert resp.status_code == 200
    body = resp.json()
    assert body['fetched'] == 1
    assert body['saved'] == 1
