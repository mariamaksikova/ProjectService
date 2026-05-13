from unittest.mock import AsyncMock, patch

import pytest

from app.notifications import publish_notification


@pytest.mark.asyncio
async def test_publish_notification_swallows_connection_error():
    with patch(
        "app.notifications.aio_pika.connect_robust",
        new=AsyncMock(side_effect=ConnectionError("no broker")),
    ):
        await publish_notification(1, "t", "body")


