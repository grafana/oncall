from unittest.mock import MagicMock

import pytest

from apps.slack.slack_formatter import SlackFormatter


@pytest.mark.django_db
def test_slack_to_accepted_emoji():
    sf = SlackFormatter(MagicMock())
    test_message = """[:book: Runbook:link:](https://example-test.com/explore?panes=%7B:%7Bname-with-dash%22:%22FE%22:%5B%7B%22another-one%22:namespace-with-dash)
Test emoji :male-construction-worker:https://another-example.com/test:=%22-dash
:female-construction-worker:"""
    expected_result = test_message.replace("-construction-worker", "_construction_worker")
    result = sf.slack_to_accepted_emoji(test_message)
    assert result == expected_result
