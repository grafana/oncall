# requires: requests

import requests
from datetime import datetime, timedelta

HOURS_DELTA = -1  # delta in hours to shift rotations
ONCALL_API_BASE_URL = "https://oncall-prod-us-central-0.grafana.net/oncall"
ONCALL_API_TOKEN = "<oncall API token>"
# update only a specific schedule, by id (e.g. "SVVGWD8W1Q38A")
# if set to None, will update all your schedules
SCHEDULE_ID = None

headers = {
    "Authorization": ONCALL_API_TOKEN,
}

if SCHEDULE_ID is not None:
    # filter schedule shifts
    url = f"{ONCALL_API_BASE_URL}/api/v1/on_call_shifts/?schedule_id={SCHEDULE_ID}"
else:
    # assuming there is up to 100 shifts only (max page size)
    url = f"{ONCALL_API_BASE_URL}/api/v1/on_call_shifts/?perpage=100"

# note: overrides are not included
r = requests.get(url, headers=headers)
if not r.ok:
    raise Exception(r.status_code)

now = datetime.utcnow()
shift_delta = timedelta(hours=HOURS_DELTA)
shifts = r.json()["results"]
for shift in shifts:
    # get shift information
    shift_id = shift["id"]
    shift_start = datetime.strptime(shift["start"], "%Y-%m-%dT%H:%M:%S")
    until = shift.get("until")
    if until is not None:
        until = datetime.strptime(shift["start"], "%Y-%m-%dT%H:%M:%S")
        if until < now:
            # skip finished rotation
            continue
    # update shift start by delta
    updated_start = shift_start + shift_delta
    update_data = {"start": updated_start.isoformat()}
    shift_url = f"{ONCALL_API_BASE_URL}/api/v1/on_call_shifts/{shift_id}"
    r = requests.put(shift_url, json=update_data, headers=headers)
    if not r.ok:
        print(f"Failed to update shift {shift_id}")
    else:
        print(f"Shift {shift_id} updated")
  