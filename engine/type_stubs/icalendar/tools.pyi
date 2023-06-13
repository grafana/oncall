from _typeshed import Incomplete
from icalendar.parser_tools import to_unicode as to_unicode
from icalendar.prop import vDatetime as vDatetime
from icalendar.prop import vText as vText

class UIDGenerator:
    chars: Incomplete
    def rnd_string(self, length: int = ...): ...
    def uid(self, host_name: str = ..., unique: str = ...): ...
