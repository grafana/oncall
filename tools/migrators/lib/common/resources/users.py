import typing


class MatchUser(typing.TypedDict):
    email: str
    oncall_user: typing.Optional[typing.Dict[str, typing.Any]]


def match_user(user: MatchUser, oncall_users: typing.List[MatchUser]) -> None:
    oncall_user = None
    for candidate_user in oncall_users:
        if user["email"].lower() == candidate_user["email"].lower():
            oncall_user = candidate_user
            break

    user["oncall_user"] = oncall_user
