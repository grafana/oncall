<img width="400px" src="docs/img/logo.png">

Developer-friendly, incident response management with brilliant Slack integration.

<img width="60%" src="screenshot.png">

- Collect and analyze alerts from multiple monitoring systems
- On-call rotations based on schedules
- Automatic escalations
- Phone calls, SMS, Slack, Telegram notifications

## Getting Started

We prepared multiple environments: [production](PRODUCTION.md), [developer](DEVELOPER.md) and hobby:

1. Download docker-compose.yaml:
```bash
curl https://github.com/grafana/oncall/blob/dev/docker-compose.yml -o docker-compose.yaml 
```

2. Set variables:
```bash
export DOMAIN=http://localhost
export SECRET_KEY=my_random_secret_must_be_more_than_32_characters_long
export RABBITMQ_PASSWORD=rabbitmq_secret_pw
export MYSQL_PASSWORD=mysql_secret_pw
export COMPOSE_PROFILES=with_grafana  # Comment this line if you want to use existing grafana
export GRAFANA_USER=admin
export GRAFANA_PASSWORD=admin
```

3. Launch services:
```bash
docker-compose -f docker-compose.yml up --build -d
```

4. Issue one-time invite token:
```bash
docker-compose -f docker-compose.yml run engine python manage.py issue_invite_for_the_frontend --override
```

5. Go to [OnCall Plugin Configuration](http://localhost:3000/plugins/grafana-oncall-app) (or find OnCall plugin in configuration->plugins) and connect OnCall _plugin_ with OnCall _backend_:
```
Invite token: ^^^ from the previous step.
OnCall backend URL: http://engine:8080
Grafana Url: http://grafana:3000
```

6. Enjoy!


## Join community

<a href="https://github.com/grafana/oncall/discussions/categories/community-calls"><img width="200px" src="docs/img/community_call.png"></a>
<a href="https://github.com/grafana/oncall/discussions"><img width="200px" src="docs/img/GH_discussions.png"></a>
<a href="https://slack.grafana.com/"><img width="200px" src="docs/img/slack.png"></a>

## Further Reading
- *Documentation* - [Grafana OnCall](https://grafana.com/docs/grafana-cloud/oncall/)
- *Blog Post* - [Announcing Grafana OnCall, the easiest way to do on-call management](https://grafana.com/blog/2021/11/09/announcing-grafana-oncall/)
- *Presentation* - [Deep dive into the Grafana, Prometheus, and Alertmanager stack for alerting and on-call management](https://grafana.com/go/observabilitycon/2021/alerting/?pg=blog)
