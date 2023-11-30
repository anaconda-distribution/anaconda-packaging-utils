"""
File:           types.py
Description:    File that contains common types and type aliases (typedefs).
"""
from typing import Final, Union

# Base types that can store value
Primitives = Union[str, int, float, bool, None]
# Same primitives, as a tuple. Used with `isinstance()`
PRIMITIVES_TUPLE: Final[tuple[type[str], type[int], type[float], type[bool], type[None]]] = (
    str,
    int,
    float,
    bool,
    type(None),
)

# Type that represents a JSON-like type
JsonType = Union[dict[str, "JsonType"], list["JsonType"], Primitives]
# Represents a JSON object structure. Casting to this on a validated JSON object should alleviate static analyzer
# index errors.
JsonObjectType = dict[str, JsonType]

# Types that build up to types used in `jsonschema`s
SchemaPrimitives = Union[str, int, bool, None]
SchemaDetails = Union[dict[str, "SchemaDetails"], list["SchemaDetails"], SchemaPrimitives]
# Type for a schema object used by the `jsonschema` library
SchemaType = dict[str, SchemaDetails]


# All sentinel values used in this module should be constructed with this class, for typing purposes.
class SentinelType:
    pass


# Common exit codes
EXIT_SUCCESS: Final[int] = 0
EXIT_FAILURE: Final[int] = 1
EXIT_CRITICAL_EXCEPTION: Final[int] = 42
