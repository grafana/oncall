import argparse
import asyncio
import math
import random
import typing
import uuid
from datetime import datetime

import aiohttp
from faker import Faker
from tqdm.asyncio import tqdm

fake = Faker()

TEAMS_USERS_COMMAND = "generate_teams_and_users"
SCHEDULES_ONCALL_SHIFTS_COMMAND = "generate_schedules_and_oncall_shifts"

GRAFANA_API_URL = None
ONCALL_API_URL = None
ONCALL_API_TOKEN = None


class OnCallApiUser(typing.TypedDict):
    id: str


class OnCallApiOnCallShift(typing.TypedDict):
    id: str


class OnCallApiListUsersResponse(typing.TypedDict):
    results: typing.List[OnCallApiUser]


class GrafanaAPIUser(typing.TypedDict):
    id: int


def _generate_unique_email() -> str:
    user = fake.profile()
    return f'{uuid.uuid4()}-{user["mail"]}'


async def _grafana_api_request(
    http_session: aiohttp.ClientSession, method: str, url: str, **request_kwargs
) -> typing.Awaitable[typing.Dict]:
    resp = await http_session.request(
        method, f"{GRAFANA_API_URL}{url}", **request_kwargs
    )
    return await resp.json()


async def _oncall_api_request(
    http_session: aiohttp.ClientSession, method: str, url: str, **request_kwargs
) -> typing.Awaitable[typing.Dict]:
    resp = await http_session.request(
        method,
        f"{ONCALL_API_URL}{url}",
        headers={"Authorization": ONCALL_API_TOKEN},
        **request_kwargs,
    )
    return await resp.json()


def generate_team(
    http_session: aiohttp.ClientSession, org_id: int
) -> typing.Callable[[], typing.Awaitable[typing.Dict]]:
    """
    https://grafana.com/docs/grafana/latest/developers/http_api/team/#add-team
    """

    def _generate_team() -> typing.Awaitable[typing.Dict]:
        return _grafana_api_request(
            http_session,
            "POST",
            "/api/teams",
            json={
                "name": str(uuid.uuid4()),
                "email": _generate_unique_email(),
                "orgId": org_id,
            },
        )

    return _generate_team


def generate_user(
    http_session: aiohttp.ClientSession, org_id: int
) -> typing.Callable[[], typing.Awaitable[typing.Dict]]:
    """
    https://grafana.com/docs/grafana/latest/developers/http_api/admin/#global-users
    """

    async def _generate_user() -> typing.Awaitable[typing.Dict]:
        user = fake.profile()

        # create the user in grafana
        grafana_user: GrafanaAPIUser = await _grafana_api_request(
            http_session,
            "POST",
            "/api/admin/users",
            json={
                "name": user["name"],
                "email": _generate_unique_email(),
                "login": str(uuid.uuid4()),
                "password": fake.password(length=20),
                "OrgId": org_id,
            },
        )

        # update the user's basic role in grafana to Admin
        # https://grafana.com/docs/grafana/latest/developers/http_api/org/#updates-the-given-user
        await _grafana_api_request(
            http_session,
            "PATCH",
            f'/api/org/users/{grafana_user["id"]}',
            json={"role": "Admin"},
        )

        return grafana_user

    return _generate_user


def generate_schedule(
    http_session: aiohttp.ClientSession, oncall_shift_ids: typing.List[str]
) -> typing.Callable[[], typing.Awaitable[typing.Dict]]:
    def _generate_schedule() -> typing.Awaitable[typing.Dict]:
        # Create a schedule
        # https://grafana.com/docs/oncall/latest/oncall-api-reference/schedules/#create-a-schedule
        return _oncall_api_request(
            http_session,
            "POST",
            "/api/v1/schedules",
            json={
                "name": f"Schedule {uuid.uuid4()}",
                "type": "calendar",
                "time_zone": "UTC",
                "shifts": oncall_shift_ids,
            },
        )

    return _generate_schedule


def _bulk_generate_data(
    iterations: int,
    data_generator_func: typing.Callable[[], typing.Awaitable[typing.Dict]],
) -> typing.Awaitable[typing.List[typing.Dict]]:
    return tqdm.gather(
        *[asyncio.ensure_future(data_generator_func()) for _ in range(iterations)]
    )


async def _generate_grafana_teams_and_users(
    args: argparse.Namespace, http_session: aiohttp.ClientSession
) -> typing.Awaitable[None]:
    global GRAFANA_API_URL
    GRAFANA_API_URL = args.grafana_api_url

    org_id = args.grafana_org_id

    print("Generating team(s)")
    await _bulk_generate_data(args.teams, generate_team(http_session, org_id))

    print("Generating user(s)")
    await _bulk_generate_data(args.users, generate_user(http_session, org_id))

    print(
        f"""
    Grafana teams and users generated
    Now head to the OnCall plugin and manually visit the plugin to trigger a sync. This will sync grafana
    teams/users to OnCall. Once completed, you can run the {SCHEDULES_ONCALL_SHIFTS_COMMAND} command.
    """
    )


async def _generate_oncall_schedules_and_oncall_shifts(
    args: argparse.Namespace, http_session: aiohttp.ClientSession
) -> typing.Awaitable[None]:
    global ONCALL_API_URL, ONCALL_API_TOKEN
    ONCALL_API_URL = args.oncall_api_url
    ONCALL_API_TOKEN = args.oncall_api_token

    today = datetime.now()

    print("Fetching users from OnCall API")

    # Fetch users from the OnCall API
    users: OnCallApiListUsersResponse = await _oncall_api_request(
        http_session, "GET", "/api/v1/users"
    )
    user_ids: typing.List[str] = [u["id"] for u in users["results"]]
    num_users = len(user_ids)

    print(f"Fetched {num_users} user(s) from the OnCall API")

    async def _create_oncall_shift(shift_start_time: str) -> typing.Awaitable[str]:
        """
        Creates an eight hour shift.

        `shift_start_time` - ex. 09:00:00, 15:00:00

        https://grafana.com/docs/oncall/latest/oncall-api-reference/on_call_shifts/#create-an-oncall-shift
        """
        new_shift: OnCallApiOnCallShift = await _oncall_api_request(
            http_session,
            "POST",
            "/api/v1/on_call_shifts",
            json={
                "name": f"On call shift{uuid.uuid4()}",
                "type": "rolling_users",
                "start": today.strftime(f"%Y-%m-%dT{shift_start_time}"),
                "time_zone": "UTC",
                "duration": 60 * 60 * 8,  # 8 hours
                "frequency": "daily",
                "week_start": "MO",
                "rolling_users": [
                    [u] for u in random.choices(user_ids, k=math.floor(num_users / 2))
                ],
                "start_rotation_from_user_index": 0,
                "team_id": None,
            },
        )

        oncall_shift_id = new_shift["id"]
        print(f"Generated OnCall shift w/ ID {oncall_shift_id}")
        return oncall_shift_id

    print("Creating three 8h on-call shifts")
    morning_shift_id = await _create_oncall_shift("00:00:00")
    afternoon_shift_id = await _create_oncall_shift("08:00:00")
    evening_shift_id = await _create_oncall_shift("16:00:00")

    print("Generating schedules(s)")
    await _bulk_generate_data(
        args.schedules,
        generate_schedule(
            http_session, [morning_shift_id, afternoon_shift_id, evening_shift_id]
        ),
    )


async def main() -> typing.Awaitable[None]:
    parser = argparse.ArgumentParser(
        description="Set of commands to help generate fake data in a Grafana OnCall setup."
    )
    subparsers = parser.add_subparsers(help="sub-command help")

    grafana_command_parser = subparsers.add_parser(
        TEAMS_USERS_COMMAND,
        description="Command to generate teams and users in Grafana",
    )
    grafana_command_parser.set_defaults(func=_generate_grafana_teams_and_users)
    grafana_command_parser.add_argument(
        "--grafana-api-url",
        help="Grafana API URL. This should include the basic authentication username/password in the URL. ex. http://oncall:oncall@localhost:3000",
        default="http://oncall:oncall@localhost:3000",
    )
    grafana_command_parser.add_argument(
        "--grafana-org-id",
        help="Org ID, in Grafana, of the org that you would like to generate data for",
        type=int,
        default=1,
    )
    grafana_command_parser.add_argument(
        "-t", "--teams", help="Number of teams to generate", default=10, type=int
    )
    grafana_command_parser.add_argument(
        "-u", "--users", help="Number of users to generate", default=1_000, type=int
    )

    oncall_command_parser = subparsers.add_parser(
        SCHEDULES_ONCALL_SHIFTS_COMMAND,
        description="Command to generate schedules and on-call shifts in OnCall",
    )
    oncall_command_parser.set_defaults(
        func=_generate_oncall_schedules_and_oncall_shifts
    )
    oncall_command_parser.add_argument(
        "--oncall-api-url",
        help="OnCall API URL",
        default="http://localhost:8080",
    )
    oncall_command_parser.add_argument(
        "--oncall-api-token", help="OnCall API token", required=True
    )
    oncall_command_parser.add_argument(
        "-s",
        "--schedules",
        help="Number of schedules to generate",
        default=100,
        type=int,
    )

    args = parser.parse_args()

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=5)
    ) as session:
        await args.func(args, session)


if __name__ == "__main__":
    asyncio.run(main())
