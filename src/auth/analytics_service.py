from auth.kafka_producer import KafkaProducer
from auth.schemas import Event


class AnalyticsService:
    def __init__(self, producer: KafkaProducer):
        self.producer = producer

    async def publish_event(self, topic: str, event: Event):
        await self.producer.produce_message(topic, event)
