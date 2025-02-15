from dependency_injector import containers, providers

from config import VersionConfig


class VersionContainer(containers.DeclarativeContainer):
    version_config = providers.Singleton(VersionConfig)
