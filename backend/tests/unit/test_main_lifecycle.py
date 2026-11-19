import asyncio
from unittest.mock import patch
import pytest

from backend.src.main import periodic_cleanup

@pytest.mark.asyncio
async def test_periodic_cleanup_executes_and_cancels():
    called = []

    def fake_cleanup(day_number):
        called.append(day_number)

    with patch("backend.src.main.cleanup", side_effect=fake_cleanup):
        task = asyncio.create_task(periodic_cleanup(day_number=3, interval_seconds=0.01))
        # Wait briefly for periodic_cleanup to run once
        await asyncio.sleep(0.03)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    assert len(called) >= 1
    assert called[0] == 3
