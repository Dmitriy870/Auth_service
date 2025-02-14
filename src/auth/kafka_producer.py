import json
import logging
from typing import Optional

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError, KafkaTimeoutError
from dependency_injector.wiring import Provide, inject

from auth.encoder import CustomJSONEncoder
from auth.logging_conf import configurate_logging
from config import KafkaConfig
from containers.kafka import KafkaContainer

logger = configurate_logging(logging.INFO)


class KafkaProducer:
    _instance: Optional["KafkaProducer"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @inject
    def __init__(self, kafka_config: KafkaConfig = Provide[KafkaContainer.kafka_config]):
        self.kafka_config = kafka_config
        if not hasattr(self, "producer"):
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_config.BOOTSTRAP_SERVERS,
            )

    async def start(self):
        await self.producer.start()
        logger.info("Kafka producer started.")

    async def stop(self):
        await self.producer.stop()
        logger.info("Kafka producer stopped.")

    async def produce_message(self, topic: str, data: dict):
        logger.info("before producer start")
        await self.start()
        try:
            logger.info("Start producing message(with serialize)")
            # if isinstance(data, BaseModel):
            #     data = data.model_dump()
            serialized_value = json.dumps(data, cls=CustomJSONEncoder).encode("utf-8")
            await self.producer.send_and_wait(topic, serialized_value)
            logger.info(f"Message sent to topic '{topic}': {data}")
        except KafkaTimeoutError:
            logger.error(f"Timeout occurred while sending message to topic '{topic}'.")
        except KafkaError as e:
            logger.error(f"Kafka error while sending message to topic '{topic}': {e}")
