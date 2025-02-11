import json
import logging
from typing import Optional

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError, KafkaTimeoutError
from pydantic import BaseModel

from auth.encoder import CustomJSONEncoder
from config import KafkaConfig

kafka_config = KafkaConfig()
logger = logging.getLogger(__name__)


class KafkaProducerSingleton:
    _instance: Optional["KafkaProducerSingleton"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "producer"):
            self.producer = AIOKafkaProducer(bootstrap_servers="kafka:9092")

    async def start(self):
        await self.producer.start()
        logger.info("Kafka producer started.")

    async def stop(self):
        await self.producer.stop()
        logger.info("Kafka producer stopped.")

    async def produce_message(self, topic: str, data: dict):
        logger.info("before start")
        await self.start()
        try:
            logger.info("In try block")
            if isinstance(data, BaseModel):
                data = data.model_dump()
            serialized_value = json.dumps(data, cls=CustomJSONEncoder).encode("utf-8")
            await self.producer.send_and_wait(topic, serialized_value)
            logger.info(f"Message sent to topic '{topic}': {data}")
        except KafkaTimeoutError:
            logger.error(f"Timeout occurred while sending message to topic '{topic}'.")
        except KafkaError as e:
            logger.error(f"Kafka error while sending message to topic '{topic}': {e}")
