from dependency_injector import containers, providers

from config import FileConfig


class FileConfigContainer(containers.DeclarativeContainer):
    file_config = providers.Singleton(FileConfig)
