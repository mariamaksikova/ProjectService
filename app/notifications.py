import asyncio
import json
import os
import aio_pika
from typing import Optional

async def publish_notification(
    user_id: int,
    title: str,
    content: str,
    email: Optional[str] = None
):
    """
    Отправляет уведомление в RabbitMQ
    
    Args:
        user_id: ID пользователя (из JWT)
        title: Заголовок уведомления
        content: Содержание уведомления
        email: Email пользователя (опционально, из JWT)
    """
    amqp_url = (
        f"amqp://{os.getenv('RABBITMQ_USER', 'guest')}:"
        f"{os.getenv('RABBITMQ_PASSWORD', 'guest')}@"
        f"{os.getenv('RABBITMQ_HOST', 'localhost')}/"
    )
    
    data = {
        "user_id": user_id,
        "title": title,
        "content": content
    }
    
    if email:
        data["email"] = email
    
    try:
        connection = await aio_pika.connect_robust(amqp_url)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(data).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="notifications"
            )
    except Exception as e:
        # Логируем ошибку, но не блокируем основной процесс
        print(f"Failed to send notification: {e}")