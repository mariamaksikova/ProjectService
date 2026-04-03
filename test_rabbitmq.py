import asyncio
from app.notifications import publish_notification

async def test():
    await publish_notification(
        user_id=1,
        title="Тест",
        content="Проверка отправки уведомления"
    )
    print("✅ Сообщение отправлено!")

if __name__ == "__main__":
    asyncio.run(test())