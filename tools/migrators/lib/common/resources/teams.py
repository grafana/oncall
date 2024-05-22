import typing


class MatchTeam(typing.TypedDict):
    name: str
    oncall_team: typing.Optional[typing.Dict[str, typing.Any]]


def match_team(team: MatchTeam, oncall_teams: typing.List[MatchTeam]) -> None:
    oncall_team = None
    for candidate_team in oncall_teams:
        if team["name"].lower() == candidate_team["name"].lower():
            oncall_team = candidate_team
            break

    team["oncall_team"] = oncall_team
