# PagerDuty migrator scripts

When running the migrator in `plan` mode, it can potentially show that some users cannot be matched
(meaning that there are no users in Grafana with the same email as in PagerDuty).

If there is a large number of unmatched users, it can be easier to use the following script that
automatically creates missing Grafana users:

```bash
docker run --rm \
-e PAGERDUTY_API_TOKEN="<PAGERDUTY_API_TOKEN>" \
-e GRAFANA_URL="http://localhost:3000" \
-e GRAFANA_USERNAME="admin" \
-e GRAFANA_PASSWORD="admin" \
pd-oncall-migrator python /app/scripts/add_users_pagerduty_to_grafana.py
```

The script will create users with random passwords, so they will need to reset their passwords later in Grafana.
