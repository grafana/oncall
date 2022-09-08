# PagerDuty migrator scripts

When we run MODE="plan" we can notice that there is escalation, integration in pagerduty that needs to be linked to a user.

To solve this problem, we can run the  add_users_pagerduty_to_grafana.py script

```bash
docker run -it --rm -e PAGERDUTY_API_TOKEN="mytoken" -e URL_GRAFANA="http://localhost:3000" -e USERNAME_GRAFANA="admin" -e PASSWORD_GRAFANA="admin" pd-oncall-migrator python /app/scripts/add_users_pagerduty_to_grafana.py
```