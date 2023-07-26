import pytest

from apps.alerts.models import ChannelFilter


@pytest.mark.django_db
def test_channel_filter_select_filter(make_organization, make_alert_receive_channel, make_channel_filter):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    filtering_term = "test alert"
    channel_filter = make_channel_filter(alert_receive_channel, filtering_term=filtering_term, is_default=False)

    title = "Test Title"

    # alert with data which includes custom route filtering term, satisfied filter is custom channel filter
    raw_request_data = {"title": filtering_term}
    satisfied_filter = ChannelFilter.select_filter(alert_receive_channel, raw_request_data)
    assert satisfied_filter == channel_filter

    # alert with data which does not include custom route filtering term, satisfied filter is default channel filter
    raw_request_data = {"title": title}
    satisfied_filter = ChannelFilter.select_filter(alert_receive_channel, raw_request_data)
    assert satisfied_filter == default_channel_filter

    # demo alert for custom route
    raw_request_data = {"title": "i'm not matching this route"}
    satisfied_filter = ChannelFilter.select_filter(
        alert_receive_channel, raw_request_data, force_route_id=channel_filter.pk
    )
    assert satisfied_filter == channel_filter


@pytest.mark.django_db
def test_channel_filter_select_filter_regex(make_organization, make_alert_receive_channel, make_channel_filter):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    filtering_term = "test alert"
    channel_filter = make_channel_filter(
        alert_receive_channel,
        filtering_term=filtering_term,
        filtering_term_type=ChannelFilter.FILTERING_TERM_TYPE_REGEX,
        is_default=False,
    )

    # alert with data which includes custom route filtering term, satisfied filter is custom channel filter
    raw_request_data = {"title": filtering_term}
    satisfied_filter = ChannelFilter.select_filter(alert_receive_channel, raw_request_data)
    assert satisfied_filter == channel_filter

    # alert with data which does not include custom route filtering term, satisfied filter is default channel filter
    raw_request_data = {"title": "Test Title"}
    satisfied_filter = ChannelFilter.select_filter(alert_receive_channel, raw_request_data)
    assert satisfied_filter == default_channel_filter

    # demo alert for custom route
    raw_request_data = {"title": "i'm not matching this route"}
    satisfied_filter = ChannelFilter.select_filter(
        alert_receive_channel, raw_request_data, force_route_id=channel_filter.pk
    )
    assert satisfied_filter == channel_filter


@pytest.mark.django_db
def test_channel_filter_select_filter_jinja2(make_organization, make_alert_receive_channel, make_channel_filter):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    filtering_term = '{{ payload.foo == "bar" }}'
    channel_filter = make_channel_filter(
        alert_receive_channel,
        filtering_term=filtering_term,
        filtering_term_type=ChannelFilter.FILTERING_TERM_TYPE_JINJA2,
        is_default=False,
    )

    # alert with data which includes custom route filtering term, satisfied filter is custom channel filter
    raw_request_data = {"foo": "bar"}
    satisfied_filter = ChannelFilter.select_filter(alert_receive_channel, raw_request_data)
    assert satisfied_filter == channel_filter

    # alert with data which does not include custom route filtering term, satisfied filter is default channel filter
    raw_request_data = {"foo": "qaz"}
    satisfied_filter = ChannelFilter.select_filter(alert_receive_channel, raw_request_data)
    assert satisfied_filter == default_channel_filter

    # demo alert for custom route
    raw_request_data = {"title": "i'm not matching this route"}
    satisfied_filter = ChannelFilter.select_filter(
        alert_receive_channel, raw_request_data, force_route_id=channel_filter.pk
    )
    assert satisfied_filter == channel_filter
