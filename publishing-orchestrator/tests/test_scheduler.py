from src.main import schedule_platform_publication, PlatformConfig
import asyncio

def test_scheduler_returns_job_id():
    cfg = PlatformConfig(enabled=True, account_id="acc")
    job = asyncio.get_event_loop().run_until_complete(
        schedule_platform_publication("twitter", {"content": "x"}, cfg)
    )
    assert job.startswith("twitter_")
