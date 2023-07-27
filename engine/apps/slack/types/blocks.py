"""
[Documentation](https://api.slack.com/reference/block-kit/blocks)
"""

import typing

from .block_elements import BlockElement
from .composition_objects import CompositionObjects


class Block:
    class _BaseBlock(typing.TypedDict):
        block_id: str
        """
        A string acting as a unique identifier for a block. If not specified, one will be generated.

        You can use this `block_id` when you receive an interaction payload to
        [identify the source of the action](https://api.slack.com/interactivity/handling#payloads). Maximum
        length for this field is 255 characters. `block_id` should be unique for each message and each iteration of a
        message. If a message is updated, use a new `block_id`.
        """

    class Context(_BaseBlock):
        pass

    class Input(_BaseBlock):
        """
        A block that collects information from users - it can hold a plain-text input element, a checkbox element, a
        radio button element, a select menu element, a multi-select menu element, or a datepicker.

        [Documentation](https://api.slack.com/reference/block-kit/blocks#input)
        """

        type: typing.Literal["input"]
        """
        The type of block. For an input block, `type` is always `input`.
        """

        label: CompositionObjects.PlainText
        """
        A label that appears above an input element in the form of a
        [text object](https://api.slack.com/reference/messaging/composition-objects#text) that must
        have type of `plain_text`.

        Maximum length for the text in this field is 2000 characters.
        """

        element: BlockElement.Any
        """
        A plain-text input element, a checkbox element, a radio button element, a select menu element, a multi-select
        menu element, or a datepicker.
        """

        dispatch_action: bool
        """
        A boolean that indicates whether or not the use of elements in this block should dispatch a
        [block_actions payload](https://api.slack.com/reference/interaction-payloads/block-actions).

        Defaults to `false`.
        """

        hint: CompositionObjects.PlainText
        """
        An optional hint that appears below an input element in a lighter grey.

        It must be a [text object](https://api.slack.com/reference/messaging/composition-objects#text) with a type of
        `plain_text`. Maximum length for the `text` in this field is 2000 characters.
        """

        optional: bool
        """
        A boolean that indicates whether the input element may be empty when a user submits the modal.

        Defaults to `false`.
        """

    class Section(_BaseBlock):
        """
        A `section` can be used as a simple text block, in combination with text fields, or side-by-side with certain
        [block elements](https://api.slack.com/reference/messaging/block-elements).

        [Documentation](https://api.slack.com/reference/block-kit/blocks#section)
        """

        type: typing.Literal["section"]
        """
        The type of block. For a section block, `type` will always be `section`.
        """

        text: CompositionObjects.Text
        """
        The text for the block, in the form of a [text object](https://api.slack.com/reference/block-kit/composition-objects#text).

        Minimum length for the text in this field is 1 and maximum length is 3000 characters.
        This field is not required if a valid array of fields objects is provided instead.
        """

        fields: typing.List[CompositionObjects.Text]
        """
        Required if no `text` is provided.

        An array of [text objects](https://api.slack.com/reference/messaging/composition-objects#text). Any text objects
        included with `fields` will be rendered in a compact format that allows for 2 columns of side-by-side text. Maximum number of items is 10. Maximum length for the `text` in each item is 2000 characters.
        """  # noqa: E501

        accessory: BlockElement.Any
        """
        One of the compatible [element objects](https://api.slack.com/reference/messaging/block-elements).

        Be sure to confirm the desired element works with `section`.
        """

    Any = Context | Input | Section


__all__ = [
    "Block",
]
