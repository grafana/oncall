# pip install openpyxl pytz requests

# ONCALL_API_TOKEN="<YOUR-TOKEN>" python swap_requests_workday.py -u <USER_ID> -s <SCHEDULE_ID> <workday-exported-file.xlsx> -t <TIMEZONE>
# e.g. ONCALL_API_TOKEN="the-token" python swap_requests_workday.py -u UCGEIXI1MR1NZ -s SF1R2ZQZKJNLK workday.xlsx -t "America/Montevideo" -d

# TODO: handle specific events (public holidays, vacation, sick leave, etc)

import argparse
import datetime
import os

import openpyxl
import pytz
import requests


ONCALL_API_TOKEN = os.environ.get("ONCALL_API_TOKEN", "")
ONCALL_API_BASE_URL = os.environ.get(
    "ONCALL_API_BASE_URL", "# https://oncall-prod-us-central-0.grafana.net/oncall"
)

parser = argparse.ArgumentParser(
    description="Create shift swap requests from a Workday absences exported file"
)
parser.add_argument("-d", "--dry-run", action="store_true", help="Dry run")
parser.add_argument("-u", "--user", required=True, help="User ID, swap beneficiary")
parser.add_argument("-s", "--schedule", required=True, help="Schedule ID")
parser.add_argument(
    "-t", "--timezone", required=False, default="UTC", help="User timezone"
)
parser.add_argument("filename", help="Workday export (.xlsx)")

# Read arguments from command line
args = parser.parse_args()

try:
    tz = pytz.timezone(args.timezone)
except pytz.UnknownTimeZoneError:
    raise

# shift swaps API
path = "/api/v1/shift_swaps/"
url = ONCALL_API_BASE_URL + path
# required auth
headers = {
    "Authorization": ONCALL_API_TOKEN,
}

now = datetime.datetime.now(datetime.timezone.utc)
excel = openpyxl.load_workbook(args.filename)
sheet = excel.active
for r in list(sheet.rows)[2:]:
    starting_datetime, _, absence_type, duration, unit, comment, status, _ = [
        cell.value for cell in r
    ]

    starting_datetime = tz.localize(starting_datetime).astimezone(pytz.UTC)
    if starting_datetime <= now:
        # ignore past absences
        continue

    if duration <= 0:
        # ignore corrections
        continue

    if status != "Approved":
        # only consider approved requests
        continue

    # check request already exists
    params = {
        "schedule_id": args.schedule,
        "beneficiary": args.user,
        "starting_after": starting_datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    r = requests.get(url, params=params, headers=headers)
    r.raise_for_status()
    results = r.json().get("results")
    if results and results[0]["swap_start"] == params["starting_after"]:
        print("Swap request already exists for {}".format(params["starting_after"]))
        continue

    # assert unit == "Days"
    ending_datetime = starting_datetime + datetime.timedelta(hours=24 * duration)
    description = "{}: {}".format(absence_type, comment or "I will be off")
    # create swap request
    data = {
        "schedule": args.schedule,
        "swap_start": starting_datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "swap_end": ending_datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "description": description,
        "beneficiary": args.user,
    }
    if args.dry_run:
        print("Swap request payload would be:")
        print(data)
    else:
        r = requests.post(url, json=data, headers=headers)
        r.raise_for_status()
        print(
            "Swap request created for {} ({})".format(
                params["starting_after"], absence_type
            )
        )
