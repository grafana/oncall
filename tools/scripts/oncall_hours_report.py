import csv
import requests
from datetime import datetime, timedelta

# CUSTOMIZE THE FOLLOWING VARIABLES
START_DATE = "2023-09-01"
END_DATE = "2023-09-30"
# time outside this range (or during weekends) will be considered non-working hours
WORKING_HOURS_START_TIME = timedelta(hours=0, minutes=0, seconds=0)
WORKING_HOURS_END_TIME = timedelta(hours=23, minutes=59, seconds=59)

MY_ONCALL_API_BASE_URL = "https://oncall-prod-us-central-0.grafana.net/oncall/api/v1/schedules"
MY_ONCALL_API_KEY = "<oncall API token>"
OUTPUT_FILE_NAME = f"oncall-report-{START_DATE}-to-{END_DATE}.csv"


clamp = lambda t, start, end: max(start, min(end, t))
day_delta = lambda t: t - t.replace(hour = 0, minute = 0, second = 0)


def working_hours_between(a, b):
    zero = timedelta(0)
    start = WORKING_HOURS_START_TIME
    end = WORKING_HOURS_END_TIME
    assert(zero <= start <= end <= timedelta(1))
    working_day = end - start
    days = (b - a).days + 1
    weeks = days // 7
    # exclude weekends
    if a.weekday()==0 and (b.weekday()==4 or b.weekday()==5):
        extra = 5
    else:
        extra = (max(0, 5 - a.weekday()) + min(5, 1 + b.weekday())) % 5
    weekdays = weeks * 5 + extra
    total = working_day * weekdays
    if a.weekday() < 5:
        total -= clamp(day_delta(a) - start, zero, working_day)
    if b.weekday() < 5:
        total -= clamp(end - day_delta(b), zero, working_day)
    return total


headers = {"Authorization": MY_ONCALL_API_KEY}
schedule_ids = [schedule["id"] for schedule in requests.get(MY_ONCALL_API_BASE_URL, headers=headers).json()["results"]]
user_on_call_hours = {}

for schedule_id in schedule_ids:
  response = requests.get(
    f"{MY_ONCALL_API_BASE_URL}/{schedule_id}/final_shifts?start_date={START_DATE}&end_date={END_DATE}",
    headers=headers)

  for final_shift in response.json()["results"]:
    user_pk = final_shift["user_pk"]
    end = datetime.fromisoformat(final_shift["shift_end"])
    start = datetime.fromisoformat(final_shift["shift_start"])
    shift_time_in_seconds = (end - start).total_seconds()
    shift_time_in_hours = shift_time_in_seconds / (60 * 60)
    working_hours_time = working_hours_between(start, end)
    working_hours_time_in_hours = working_hours_time.total_seconds() / (60 * 60)

    if user_pk in user_on_call_hours:
      user_on_call_hours[user_pk]["hours_on_call"] += shift_time_in_hours
      user_on_call_hours[user_pk]["working_hours_time"] += working_hours_time_in_hours
    else:
      user_on_call_hours[user_pk] = {
        "email": final_shift["user_email"],
        "hours_on_call": shift_time_in_hours,
        "working_hours_time": working_hours_time_in_hours,
      }

with open(OUTPUT_FILE_NAME, "w") as fp:
  csv_writer = csv.DictWriter(fp, ["user_pk", "user_email", "hours_on_call", "non_working_hours_on_call"])
  csv_writer.writeheader()

  for user_pk, user_info in user_on_call_hours.items():
    csv_writer.writerow({
        "user_pk": user_pk,
        "user_email": user_info["email"],
        "hours_on_call": user_info["hours_on_call"],
        "non_working_hours_on_call": user_info["hours_on_call"] - user_info["working_hours_time"],
    })
