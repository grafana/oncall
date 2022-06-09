<img width="400px" src="docs/img/logo.png">

Developer-friendly, incident response management with brilliant Slack integration.

<img width="60%" src="screenshot.png">

- Collect and analyze alerts from multiple monitoring systems
- On-call rotations based on schedules
- Automatic escalations
- Phone calls, SMS, Slack, Telegram notifications

<a href="https://github.com/grafana/oncall/discussions/categories/community-calls"><img width="200px" src="docs/img/community_call.png"></a>
<a href="https://github.com/grafana/oncall/discussions"><img width="200px" src="docs/img/GH_discussions.png"></a>
<a href="https://slack.grafana.com/"><img width="200px" src="docs/img/slack.png"></a>

## Getting Started

### Environments:

Production: [PRODUCTION.md](PRODUCTION.md).
Developer: [DEVELOPER.md](DEVELOPER.md).

### Hobby environment

Download docker-compose.yaml:
```bash
curl https://github.com/... -o docker-compose.yaml
```

Set environment:
```bash
export DOMAIN=http://localhost
export SECRET_KEY=my_random_secret_must_be_more_than_32_characters_long
export RABBITMQ_PASSWORD=rabbitmq_secret_pw
export MYSQL_PASSWORD=mysql_secret_pw
export COMPOSE_PROFILES=with_grafana
export GRAFANA_USER=admin
export GRAFANA_PASSWORD=admin
```

Launch services:
```bash
docker-compose -f docker-compose.yml up --build -d
```

Issue invite token and get further instructions:
```bash
docker-compose -f docker-compose.yml run engine python manage.py issue_invite_for_the_frontend --override
```

## Further Reading
- *Documentation* - [Grafana OnCall](https://grafana.com/docs/grafana-cloud/oncall/)
- *Blog Post* - [Announcing Grafana OnCall, the easiest way to do on-call management](https://grafana.com/blog/2021/11/09/announcing-grafana-oncall/)
- *Presentation* - [Deep dive into the Grafana, Prometheus, and Alertmanager stack for alerting and on-call management](https://grafana.com/go/observabilitycon/2021/alerting/?pg=blog)
