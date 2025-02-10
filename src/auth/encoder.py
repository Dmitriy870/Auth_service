import datetime
import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic.fields import FieldInfo


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, FieldInfo):
            return None
        if isinstance(obj, (tuple, set)):
            return list(obj)
        if isinstance(obj, dict):
            return {k: self.default(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.default(item) for item in obj]
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        return super().default(obj)
