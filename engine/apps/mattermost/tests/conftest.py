import pytest


@pytest.fixture()
def make_mattermost_get_channel_by_name_team_name_response():
    def _make_mattermost_get_channel_by_name_team_name_response():
        return {
            "id": "pbg5piuc5bgniftrserb88575h",
            "team_id": "oxfug4kgx3fx7jzow49cpxkmgo",
            "display_name": "Town Square",
            "name": "town-square",
        }

    return _make_mattermost_get_channel_by_name_team_name_response
