from typing import (
    List, 
    Dict, 
    Any, 
    TypeVar, 
    Type,
        get_origin, 
        get_args
)
from datetime import datetime, timezone

T = TypeVar('T', bound='AutoInit')
E = TypeVar('E')

import logging

class APIObject:
    def __init__(self, data_dict:Dict[str, Any]) -> None:
        for attr,_ in self.__annotations__:
            value:Any = data_dict.get(attr)
            if value:
                setattr(self, attr, value)

class AutoInit:
    def __init__(self, **kwargs:Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    @classmethod
    def from_dict(cls: Type[T], data: dict[str, object]) -> T:
        params = getattr(cls, '__annotations__', {})
        init_data: dict[str, object] = {}
        for key, field_type in params.items():
            if key in data:
                value = data[key]
                origin = get_origin(field_type)
                args = get_args(field_type)

                # Handle nested dataclass-like classes
                if hasattr(field_type, '__annotations__') and isinstance(value, dict):
                    value = field_type.from_dict(value)
                # Handle list of nested objects
                elif origin in (list, List) and args and isinstance(value, list):
                    element_type = args[0]
                    if hasattr(element_type, 'from_dict'):
                        value = [element_type.from_dict(item) if isinstance(item, dict) else item for item in value]
                init_data[key] = value
        return cls(**init_data)

class Storage(AutoInit):
    id:int
    name:str
    full_path:str

class PartLot(AutoInit):
    storage_location:Storage
    amount:int

class Category(AutoInit):
    id:int
    name:str
    full_path:str

class Part(AutoInit):
    id:int
    name:str
    manufacturer_product_number:str
    category:Category
    description:str
    partLots:List[PartLot]

class Project(AutoInit):
    id: int
    name:str
