# Fake Data Generator Script

This script can be used to easily populate fake data into your local Grafana/OnCall setup. Currently the script is
capable of generating the following objects:

- teams
- users
- schedules
- schedule on call shifts

## Prerequisites

1. Create/active a Python 3.12 virtual environment
2. `pip install -r requirements.txt`
3. Must have a local version of Grafana and OnCall up and running
4. Generate an API key inside of Grafana OnCall

## How to run

**Note**: The below flag values assume you are running a `grafana` container locally via the `docker-compose` setup.
The reason why there is a few separate steps involved is that we need to first create teams and users in the Grafana
instance. Later on, in order to create OnCall schedules/oncall-shifts, we need the OnCall user ID to do so. There is
currently no way to trigger a Grafana -> OnCall data sync via the public API, hence the manual step in the middle
to have data synced between Grafana and OnCall.

1. Create teams and users in Grafana. The `teams` and `users` flags represent the number of teams and users you would
   like to create respectively:

   ```bash
   # by default this will generate 10 teams and 1000 users
   python main.py generate_teams_and_users
   ```

   See `python main.py generate_teams_and_users -h` for more information on how to run the command.

2. Head to your OnCall setup, and trigger a Grafana -> OnCall data sync by visiting the plugin page.
3. Create schedules and on call shifts in OnCall. The `schedules` flag represents the number of OnCall schedules you
   would like to generate. **Note** that one on call shift is created for each schedule:

   ```bash
   # by default this will generate 100 schedules
   python main.py generate_schedules_and_oncall_shifts --oncall-api-token=<oncall-api-key>
   ```

   See `python main.py generate_schedules_and_oncall_shifts -h` for more information on how to run the command.
