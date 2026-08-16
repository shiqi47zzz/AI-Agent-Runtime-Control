import pytest

from agent_api_guard.controls import CapacityRejected, ConcurrencyLimit


@pytest.mark.asyncio
async def test_rejects_above_limit_and_restores_capacity() -> None:
    control = ConcurrencyLimit(1)

    async with control.admission(None):  # type: ignore[arg-type]
        with pytest.raises(CapacityRejected):
            async with control.admission(None):  # type: ignore[arg-type]
                pass

    async with control.admission(None):  # type: ignore[arg-type]
        pass
