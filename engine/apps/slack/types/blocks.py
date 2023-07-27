import typing

from .common import Text


class BaseBlockElement(typing.TypedDict):
    action_id: str
    """
    An identifier for this action. You can use this when you receive an interaction payload to
    [identify the source of the action](https://api.slack.com/interactivity/handling#payloads). Should be unique among
    all other `action_id`s in the containing block. Maximum length for this field is 255 characters.
    """


class ButtonElement(BaseBlockElement):
    type: typing.Literal["button"]
    """
    The type of element. In this case `type` is always `button`.
    """

    text: Text
    """
    A [text object](https://api.slack.com/reference/block-kit/composition-objects#text) that defines the button's text.

    Can only be of `type: plain_text`. `text` may truncate with ~30 characters. Maximum length for the `text` in this
    field is 75 characters.
    """

    style: typing.Literal["default", "primary", "danger"] | None
    """
    Decorates buttons with alternative visual color schemes. Use this option with restraint.

    `primary` gives buttons a green outline and text, ideal for affirmation or confirmation actions. `primary` should
    only be used for one button within a set.

    `danger` gives buttons a red outline and text, and should be used when the action is destructive. Use `danger` even more sparingly than `primary`.

    If you don't include this field, the `default` button style will be used.
    """


BlockElement = ButtonElement
