"""
[Documentation](https://api.slack.com/reference/block-kit/composition-objects)
"""

import typing

from .common import Style


class _TextBase(typing.TypedDict):
    """
    An object containing some text, formatted either as `plain_text` or using `mrkdwn`.

    [Documentation](https://api.slack.com/reference/block-kit/composition-objects#text)
    """

    type: typing.Literal["plain_text"] | typing.Literal["mrkdwn"]
    """
    The formatting to use for this text object. Can be one of `plain_text` or `mrkdwn`.
    """

    text: str
    """
    The text for the block. This field accepts any of the standard
    [text formatting markup](https://api.slack.com/reference/surfaces/formatting) when `type` is `mrkdwn`.
    The minimum length is 1 and maximum length is 3000 characters.
    """

    emoji: typing.Optional[bool]
    """
    Indicates whether emojis in a text field should be escaped into the colon emoji format.

    This field is only usable when `type` is `plain_text`.
    """

    verbatim: typing.Optional[bool]
    """
    When set to `false` (as is default) URLs will be auto-converted into links, conversation names will be link-ified,
    and certain mentions will be automatically parsed.

    Using a value of `true` will skip any preprocessing of this nature, although you can still include
    [manual parsing strings](https://api.slack.com/reference/surfaces/formatting#advanced). This field is only usable
    when `type` is `mrkdwn`.
    """


class CompositionObjectPlainText(_TextBase):
    type: typing.Literal["plain_text"]
    """
    The formatting to use for this text object.
    """


class CompositionObjectMrkdwnText(_TextBase):
    type: typing.Literal["mrkdwn"]
    """
    The formatting to use for this text object.
    """


CompositionObjectText = CompositionObjectPlainText | CompositionObjectMrkdwnText


class CompositionObjectOption(typing.TypedDict):
    """
    An object that represents a single selectable item in a select menu, multi-select menu, checkbox group, radio button group, or overflow menu.

    [Documentation](https://api.slack.com/reference/block-kit/composition-objects#option)
    """

    text: CompositionObjectText
    """
    A [text object](https://api.slack.com/reference/block-kit/composition-objects#text) that defines the text shown in
    the option on the menu.

    Overflow, select, and multi-select menus can only use `plain_text` objects, while radio buttons and checkboxes can
    use `mrkdwn` text objects. Maximum length for the text in this field is 75 characters.
    """

    value: str
    """
    A unique string value that will be passed to your app when this option is chosen.

    Maximum length for this field is 75 characters.
    """

    description: typing.Optional[CompositionObjectPlainText]
    """
    A [plain_text-only text object](https://api.slack.com/reference/block-kit/composition-objects#confirm:~:text=A-,plain_text,%2Donly%20text%20object,-that%20defines%20the)
    that defines a line of descriptive text shown below the `text` field beside the radio button.

    Maximum length for the `text` object within this field is 75 characters.
    """

    url: typing.Optional[str]
    """
    A URL to load in the user's browser when the option is clicked.

    The `url` attribute is only available in
    [overflow menus](https://api.slack.com/reference/block-kit/block-elements#overflow). Maximum length for this field
    is 3000 characters. If you're using `url`, you'll still receive an
    [interaction payload](https://api.slack.com/interactivity/handling#payloads) and will need to
    [send an acknowledgement response](https://api.slack.com/interactivity/handling#acknowledgment_response).
    """


class CompositionObjectOptionGroup(typing.TypedDict):
    """
    Provides a way to group options in a [select menu](https://api.slack.com/reference/block-kit/block-elements#select)
    or [multi-select menu](https://api.slack.com/reference/block-kit/block-elements#multi_select).

    [Documentation](https://api.slack.com/reference/block-kit/composition-objects#option_group)
    """

    label: CompositionObjectPlainText
    """
    A [plain_text only text object](https://api.slack.com/reference/block-kit/composition-objects#text) that defines
    the label shown above this group of options.

    Maximum length for the `text` in this field is 75 characters.
    """

    options: typing.List[CompositionObjectOption]
    """
    An array of [option objects](https://api.slack.com/reference/block-kit/composition-objects#option) that belong to
    this specific group.

    Maximum of 100 items.
    """


class CompositionObjectConfirm(typing.TypedDict):
    """
    An object that defines a dialog that provides a confirmation step to any interactive element.
    This dialog will ask the user to confirm their action by offering a confirm and deny buttons.

    [Documentation](https://api.slack.com/reference/block-kit/composition-objects#confirm)
    """

    title: CompositionObjectPlainText
    """
    A [plain_text-only text object](https://api.slack.com/reference/block-kit/composition-objects#confirm:~:text=A-,plain_text,%2Donly%20text%20object,-that%20defines%20the)
    that defines the dialog's title.

    Maximum length for this field is 100 characters.
    """

    text: CompositionObjectPlainText
    """
    A [plain_text-only text object](https://api.slack.com/reference/block-kit/composition-objects#confirm:~:text=A-,plain_text,%2Donly%20text%20object,-that%20defines%20the)
    that defines the explanatory text that appears in the confirm dialog.

    Maximum length for the text in this field is 300 characters.
    """

    confirm: CompositionObjectPlainText
    """
    A [plain_text-only text object](https://api.slack.com/reference/block-kit/composition-objects#confirm:~:text=A-,plain_text,%2Donly%20text%20object,-that%20defines%20the)
    to define the text of the button that confirms the action.

    Maximum length for the text in this field is 30 characters.
    """

    deny: CompositionObjectPlainText
    """
    A [plain_text-only text object](https://api.slack.com/reference/block-kit/composition-objects#confirm:~:text=A-,plain_text,%2Donly%20text%20object,-that%20defines%20the)
    to define the text of the button that cancels the action.

    Maximum length for the text in this field is 30 characters.
    """

    style: typing.Literal[Style.DANGER, Style.PRIMARY] | None
    """
    Defines the color scheme applied to the confirm button.

    A value of `danger` will display the button with a red background on desktop, or red text on mobile. A value of
    `primary` will display the button with a green background on desktop, or blue text on mobile.

    If this field is not provided, the default value will be `primary`.
    """
