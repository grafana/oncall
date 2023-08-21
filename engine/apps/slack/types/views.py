import typing

from .blocks import Block
from .composition_objects import CompositionObjectPlainText


class ModalView(typing.TypedDict):
    """
    [Documentation](https://api.slack.com/surfaces/modals#view-object-fields)
    """

    type: typing.Literal["modal"]
    """
    Required. The type of view. Set to `modal` for modals.
    """

    title: CompositionObjectPlainText
    """
    Required. The title that appears in the top-left of the modal.

    Must be a [plain_text text element](https://api.slack.com/reference/block-kit/composition-objects#text) with a max
    length of 24 characters.
    """

    blocks: Block.AnyBlocks
    """
    Required. An array of [blocks](https://api.slack.com/reference/block-kit/blocks) that defines the content of the
    view.

    Max of 100 blocks.
    """

    close: CompositionObjectPlainText
    """
    An optional [plain_text text element](https://api.slack.com/reference/block-kit/composition-objects#text) that
    defines the text displayed in the close button at the bottom-right of the view.

    Max length of 24 characters.
    """

    submit: CompositionObjectPlainText
    """
    An optional [plain_text text element](https://api.slack.com/reference/block-kit/composition-objects#text) that
    defines the text displayed in the submit button at the bottom-right of the view.

    `submit` is required when an input block is within the blocks array.

    Max length of 24 characters.
    """

    private_metadata: str
    """
    An optional string that will be sent to your app in `view_submission` and `block_actions` events.

    Max length of 3000 characters.
    """

    callback_id: str
    """
    An identifier to recognize interactions and submissions of this particular view. Don't use this to store sensitive
    information (use `private_metadata` instead).

    Max length of 255 characters.
    """

    clear_on_close: bool
    """
    When set to `true`, clicking on the `close` button will clear all views in a modal and close it.

    Defaults to `false`.
    """

    notify_on_close: bool
    """
    Indicates whether Slack will send your request URL a `view_closed` event when a user clicks the `close` button.

    Defaults to `false`.
    """

    external_id: str
    """
    A custom identifier that must be unique for all views on a per-team basis.
    """

    submit_disabled: bool
    """
    When set to `true`, disables the `submit` button until the user has completed one or more inputs.

    This property is for [configuration modals](https://api.slack.com/reference/workflows/configuration-view).
    """
