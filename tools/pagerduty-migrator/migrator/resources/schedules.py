from migrator import oncall_api_client


def match_schedule(schedule: dict, oncall_schedules: list[dict]) -> None:
    oncall_schedule = None
    for candidate in oncall_schedules:
        if schedule["name"].lower() == candidate["name"].lower():
            oncall_schedule = candidate

    schedule["oncall_schedule"] = oncall_schedule


def migrate_schedule(schedule: dict) -> None:
    if schedule["oncall_schedule"]:
        oncall_api_client.delete(
            "schedules/{}".format(schedule["oncall_schedule"]["id"])
        )

    payload = {
        "name": schedule["name"],
        "type": "ical",
        "ical_url_primary": schedule["http_cal_url"],
        "team_id": None,
    }
    oncall_schedule = oncall_api_client.create("schedules", payload)

    schedule["oncall_schedule"] = oncall_schedule
