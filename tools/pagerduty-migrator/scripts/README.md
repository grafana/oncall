# PagerDuty migrator scripts

When we run MODE="plan" we can notice that there is escalation, integration in pagerduty that needs to be linked to a user.

To solve this problem, we can run the  add_users_pagerduty_to_grafana.py script

```bash
docker run -it --rm -e PAGERDUTY_API_TOKEN="mytoken" -e GRAFANA_URL="http://localhost:3000" -e GRAFANA_USERNAME="admin" -e GRAFANA_PASSWORD="admin" pd-oncall-migrator python /app/scripts/add_users_pagerduty_to_grafana.py
```

It is worth remembering that this script will create a user with a random password.
To access with the user created, it will be necessary to change the password in grafana web.