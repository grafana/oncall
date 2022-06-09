Download docker-compose.yaml
```bash
curl https://github.com/... -o docker-compose.yaml
```

Start docker-compose stack
```bash
DOMAIN=localhost \
SECRET_KEY=my_random_secret_must_be_more_than_32_characters_long \
RABBITMQ_PASSWORD=rabbitmq_secret_pw \
MYSQL_PASSWORD=mysql_secret_pw \
COMPOSE_PROFILES=with_grafana \
GRAFANA_USER=admin \
GRAFANA_PASSWORD=grafana_secret_pw \
docker-compose -f docker-compose.yml up --build -d
```

Get the instructions and credentials
```bash
DOMAIN=localhost \
SECRET_KEY=my_random_secret_must_be_more_than_32_characters_long \
RABBITMQ_PASSWORD=rabbitmq_secret_pw \
MYSQL_PASSWORD=mysql_secret_pw \
COMPOSE_PROFILES=with_grafana \
GRAFANA_USER=admin \
GRAFANA_PASSWORD=grafana_secret_pw \
docker-compose -f docker-compose.yml run engine python manage.py issue_invite_for_the_frontend --override
```
