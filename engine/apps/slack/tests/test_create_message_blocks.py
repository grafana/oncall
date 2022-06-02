from apps.slack.utils import create_message_blocks


def test_long_text():
    original_text = "1" * 3000 + "\n" + "2" * 3000 + "\n" + "3" * 3000

    message_block_dict = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "1" * 3000 + "```"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "```" + "2" * 3000 + "```",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "```" + "3" * 3000 + "```",
            },
        },
    ]
    assert message_block_dict == create_message_blocks(original_text)


def test_truncation_long_text():
    original_text = "t" * 3000 + "\n" + "truncated"

    expected_message_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "t" * 3000 + "```",
            },
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "```truncated```"},
        },
    ]
    message_blocks = create_message_blocks(original_text)
    assert expected_message_blocks == message_blocks


def test_short_text():
    """Any short text test case"""

    original_text = "test" * 100

    message_block_dict = [{"type": "section", "text": {"type": "mrkdwn", "text": original_text}}]
    assert message_block_dict == create_message_blocks(original_text)
