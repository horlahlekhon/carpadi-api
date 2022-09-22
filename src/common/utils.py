import decimal
import json
from datetime import datetime, date
from enum import Enum
from uuid import UUID


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, (UUID, decimal.Decimal)):
            return obj.__str__()
        elif isinstance(obj, Enum):
            return obj.value
        raise TypeError(f"Type {type(obj)} not serializable")
