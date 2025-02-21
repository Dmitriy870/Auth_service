import logging

import httpx
from dependency_injector.wiring import Provide, inject
from fastapi import UploadFile

from auth.exceptions import ErrorCallingFileService
from auth.logging_conf import configurate_logging
from config import FileConfig
from containers.file_config import FileConfigContainer

logger = configurate_logging(logging.INFO)


class FileService:
    @inject
    async def load_avatar(
        self,
        file: UploadFile,
        old_file_slug: str,
        file_config: FileConfig = Provide[FileConfigContainer.file_config],
    ) -> str:
        try:
            async with httpx.AsyncClient() as client:
                files = {"file": (file.filename, file.file, file.content_type)}
                response = await client.post(file_config.UPLOAD_URL, files=files)
            if response.status_code != 200:
                raise ErrorCallingFileService("Error calling file service")
            data = response.json()
            slug = data["slug"]
            if old_file_slug:
                try:
                    async with httpx.AsyncClient() as client:
                        delete_url = f"{file_config.DELETE_URL}{old_file_slug}"
                        await client.delete(delete_url)
                except httpx.RequestError as e:
                    logger.error(f"Network error when deleting old avatar: {str(e)}")
            return slug

        except httpx.RequestError as e:
            logger.error(f"Network error when calling the file service: {str(e)}")
            raise ErrorCallingFileService("The file service is unavailable")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} from the file service")
            raise ErrorCallingFileService(f"File service error: {e.response.status_code}")

        except ValueError as e:
            logger.error(f"Invalid JSON response from the file service: {str(e)}")
            raise ErrorCallingFileService("Invalid response from the file service")
