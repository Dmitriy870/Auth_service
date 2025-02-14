from dependency_injector import containers, providers

from config import KafkaConfig


class KafkaContainer(containers.DeclarativeContainer):
    kafka_config = providers.Singleton(KafkaConfig)
