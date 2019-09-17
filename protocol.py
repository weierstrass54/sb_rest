import dataclasses
import dicttoxml
import json

from typing import Iterable


class XMLEncoder:
    content_type = "application/xml"

    def __to_dict(self, o):
        if isinstance(o, Iterable):
            return list(map(lambda x: self.__to_dict(x), o))
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return dict(o)

    def encode(self, data):
        return dicttoxml.dicttoxml(obj=self.__to_dict(data), attr_type=False)


class JsonEncoder:
    content_type = "application/json"

    class EnhancedJsonEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            if isinstance(o, frozenset):
                return list(o)
            return super().default(o)

    def encode(self, data):
        return json.dumps(data, cls=self.EnhancedJsonEncoder)