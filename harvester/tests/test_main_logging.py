import logging
import pytest

from harvester.src import main


@pytest.mark.asyncio
async def test_trigger_harvest_logs_warning_on_value_error(monkeypatch, caplog):
    async def fake_run(self, limit):
        return [], {}

    async def fake_save(self, items):
        raise ValueError("fail")

    monkeypatch.setattr(main.FetcherEngine, "run", fake_run)
    monkeypatch.setattr(main.StorageService, "save_items", fake_save)
    caplog.set_level(logging.WARNING)

    await main.trigger_harvest(limit=1)

    assert any(
        rec.levelno == logging.WARNING and "Chroma save failed" in rec.getMessage()
        for rec in caplog.records
    )


@pytest.mark.asyncio
async def test_trigger_harvest_logs_error_on_exception(monkeypatch, caplog):
    async def fake_run(self, limit):
        return [], {}

    async def fake_save(self, items):
        raise RuntimeError("boom")

    monkeypatch.setattr(main.FetcherEngine, "run", fake_run)
    monkeypatch.setattr(main.StorageService, "save_items", fake_save)
    caplog.set_level(logging.WARNING)

    await main.trigger_harvest(limit=1)

    assert any(
        rec.levelno == logging.ERROR and "Chroma save failed" in rec.getMessage()
        for rec in caplog.records
    )

