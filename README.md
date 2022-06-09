# Grafana OnCall Incident Response
Grafana OnCall, cloud version of Grafana OnCall: https://grafana.com/products/cloud/

Developer-friendly, incident response management with brilliant Slack integration.
- Connect monitoring systems
- Collect and analyze data
- On-call rotation
- Automatic escalation
- Never miss alerts with calls and SMS

![Grafana OnCall Screenshot](screenshot.png)

## Getting Started

### Launch "hobby" environment

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

Launch stack:
```bash
docker-compose -f docker-compose.yml up --build -d
```

Get the instructions and the token:
```bash
docker-compose -f docker-compose.yml run engine python manage.py issue_invite_for_the_frontend --override
```

^ follow instructions and enjoy!

## Join our comminuty
- `#grafana-oncall` channel at https://slack.grafana.com/
- Grafana Labs community forum for OnCall: https://community.grafana.com
- File an [issue](https://github.com/grafana/oncall/issues) for bugs, issues and feature suggestions.

## Production Setup

For production setup check [PRODUCTION.md](PRODUCTION.md).

## Further Reading
- *Documentation* - [Grafana OnCall](https://grafana.com/docs/grafana-cloud/oncall/)
- *Blog Post* - [Announcing Grafana OnCall, the easiest way to do on-call management](https://grafana.com/blog/2021/11/09/announcing-grafana-oncall/)
- *Presentation* - [Deep dive into the Grafana, Prometheus, and Alertmanager stack for alerting and on-call management](https://grafana.com/go/observabilitycon/2021/alerting/?pg=blog)

## FAQ

- How do I generate a new invitation token to connect plugin with a backend?
```bash
docker exec oncall-backend python manage.py issue_invite_for_the_frontend --override
```
