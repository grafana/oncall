"""
[Documentation](https://api.slack.com/reference/block-kit/blocks)
"""

import typing

from .block_elements import BlockElement
from .composition_objects import CompositionObjectPlainText, CompositionObjectText


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

    class Actions(_BaseBlock):
        """
        A block that is used to hold interactive elements.

        [Documentation](https://api.slack.com/reference/block-kit/blocks#actions)
        """

        type: typing.Literal["actions"]
        """
        The type of block. For an actions block, `type` is always `actions`.
        """

        elements: typing.List[
            BlockElement.Button | BlockElement.Select.Any | BlockElement.OverflowMenu | BlockElement.DatePicker
        ]
        """
        An array of interactive [element objects](https://api.slack.com/reference/messaging/block-elements) -
        [buttons](https://api.slack.com/reference/messaging/block-elements#button),
        [select menus](https://api.slack.com/reference/messaging/block-elements#select),
        [overflow menus](https://api.slack.com/reference/messaging/block-elements#overflow), or
        [date pickers](https://api.slack.com/reference/messaging/block-elements#datepicker).

        There is a maximum of 25 elements in each action block.
        """

    class Context(_BaseBlock):
        """
        Displays message context, which can include both images and text.

        [Documentation](https://api.slack.com/reference/block-kit/blocks#context)
        """

        type: typing.Literal["context"]
        """
        The type of block. For a context block, `type` is always `context`.
        """

        elements: typing.List[CompositionObjectText | BlockElement.Image]
        """
        An array of [image elements](https://api.slack.com/reference/messaging/block-elements#image) and
        [text objects](https://api.slack.com/reference/messaging/composition-objects#text).

        Maximum number of items is 10.
        """

    class Divider(_BaseBlock):
        """
        A content divider, like an `<hr>`, to split up different blocks inside of a message. The divider block is nice
        and neat, requiring only a `type`.

        [Documentation](https://api.slack.com/reference/block-kit/blocks#divider)
        """

        type: typing.Literal["divider"]
        """
        The type of block. For a divider block, `type` is always `divider`.
        """

    class Header(_BaseBlock):
        """
        A `header` is a plain-text block that displays in a larger, bold font. Use it to delineate between different
        groups of content in your app's surfaces.

        [Documentation](https://api.slack.com/reference/block-kit/blocks#header)
        """

        type: typing.Literal["header"]
        """
        The type of block. For a header block, `type` is always `header`.
        """

        text: CompositionObjectText
        """
        The text for the block, in the form of a [text object](https://api.slack.com/reference/block-kit/composition-objects#text).

        Maximum length for the `text` in this field is 150 characters.
        """

    class Image(_BaseBlock):
        """
        A simple image block, designed to make those cat photos really pop.

        [Documentation](https://api.slack.com/reference/block-kit/blocks#image)
        """

        type: typing.Literal["image"]
        """
        The type of block. For an image block, `type` is always `image`.
        """

        image_url: str
        """
        The URL of the image to be displayed.

        Maximum length for this field is 3000 characters.
        """

        alt_text: str
        """
        A plain-text summary of the image. This should not contain any markup.

        Maximum length for this field is 2000 characters.
        """

        title: CompositionObjectPlainText
        """
        An optional title for the image in the form of a
        [text object](https://api.slack.com/reference/messaging/composition-objects#text) that can only be of
        `type: plain_text`.

        Maximum length for the `text` in this field is 2000 characters.
        """

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

        label: CompositionObjectPlainText
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

        hint: CompositionObjectPlainText
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

        text: CompositionObjectText
        """
        The text for the block, in the form of a [text object](https://api.slack.com/reference/block-kit/composition-objects#text).

        Minimum length for the text in this field is 1 and maximum length is 3000 characters.
        This field is not required if a valid array of fields objects is provided instead.
        """

        fields: typing.List[CompositionObjectText]
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

    Any = Actions | Context | Divider | Header | Image | Input | Section
    AnyBlocks = typing.List[Any]


__all__ = [
    "Block",
]
