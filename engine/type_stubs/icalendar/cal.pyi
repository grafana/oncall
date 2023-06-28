from _typeshed import Incomplete
from icalendar.caselessdict import CaselessDict as CaselessDict
from icalendar.compat import unicode_type as unicode_type
from icalendar.parser import Contentline as Contentline
from icalendar.parser import Contentlines as Contentlines
from icalendar.parser import Parameters as Parameters
from icalendar.parser import q_join as q_join
from icalendar.parser import q_split as q_split
from icalendar.parser_tools import DEFAULT_ENCODING as DEFAULT_ENCODING
from icalendar.prop import TypesFactory as TypesFactory
from icalendar.prop import vDDDLists as vDDDLists
from icalendar.prop import vText as vText

class ComponentFactory(CaselessDict):
    def __init__(self, *args, **kwargs) -> None: ...

INLINE: Incomplete

class Component(CaselessDict):
    name: Incomplete
    required: Incomplete
    singletons: Incomplete
    multiple: Incomplete
    exclusive: Incomplete
    inclusive: Incomplete
    ignore_exceptions: bool
    subcomponents: Incomplete
    errors: Incomplete
    def __init__(self, *args, **kwargs) -> None: ...
    def __bool__(self) -> bool: ...
    __nonzero__ = __bool__
    def is_empty(self): ...
    @property
    def is_broken(self): ...
    def add(self, name, value, parameters: Incomplete | None = ..., encode: int = ...) -> None: ...
    def decoded(self, name, default=...): ...
    def get_inline(self, name, decode: int = ...): ...
    def set_inline(self, name, values, encode: int = ...) -> None: ...
    def add_component(self, component) -> None: ...
    def walk(self, name: Incomplete | None = ...): ...
    def property_items(self, recursive: bool = ..., sorted: bool = ...): ...
    @classmethod
    def from_ical(cls, st, multiple: bool = ...): ...
    def content_line(self, name, value, sorted: bool = ...): ...
    def content_lines(self, sorted: bool = ...): ...
    def to_ical(self, sorted: bool = ...): ...

class Event(Component):
    name: str
    canonical_order: Incomplete
    required: Incomplete
    singletons: Incomplete
    exclusive: Incomplete
    multiple: Incomplete
    ignore_exceptions: bool

class Todo(Component):
    name: str
    required: Incomplete
    singletons: Incomplete
    exclusive: Incomplete
    multiple: Incomplete

class Journal(Component):
    name: str
    required: Incomplete
    singletons: Incomplete
    multiple: Incomplete

class FreeBusy(Component):
    name: str
    required: Incomplete
    singletons: Incomplete
    multiple: Incomplete

class Timezone(Component):
    name: str
    canonical_order: Incomplete
    required: Incomplete
    singletons: Incomplete
    def to_tz(self): ...

class TimezoneStandard(Component):
    name: str
    required: Incomplete
    singletons: Incomplete
    multiple: Incomplete

class TimezoneDaylight(Component):
    name: str
    required: Incomplete
    singletons: Incomplete
    multiple: Incomplete

class Alarm(Component):
    name: str
    required: Incomplete
    singletons: Incomplete
    inclusive: Incomplete
    multiple: Incomplete

class Calendar(Component):
    name: str
    canonical_order: Incomplete
    required: Incomplete
    singletons: Incomplete

types_factory: Incomplete
component_factory: Incomplete
