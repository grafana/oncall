import typing


# LabelKey represents label key from label repo
class LabelKey(typing.TypedDict):
    id: str
    name: str
    prescribed: bool


# LabelValue represents one of the values associated with the LabelKey from label repo
class LabelValue(typing.TypedDict):
    id: str
    name: str
    prescribed: bool


# Label Pair is a KV pair identifying one label.
class LabelPair(typing.TypedDict):
    key: LabelKey
    value: LabelValue


# LabelOption represents key and array of available values
class LabelOption(typing.TypedDict):
    key: LabelKey
    values: typing.List[LabelValue]


# Alert Labels represents k:v pair applied to alert
AlertLabels = typing.Dict[str, str]
