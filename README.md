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
OnCall consists of two parts:
1. OnCall backend
2. "Grafana OnCall" plugin you need to install in your Grafana

### How to run OnCall backend
1. An all-in-one image of OnCall is available on docker hub to run it:
```bash
docker run -it --name oncall-backend -p 8000:8000 grafana/oncall-all-in-one
```

2. When the image starts up you will see a message like this:
```bash
👋 This script will issue an invite token to securely connect the frontend.
Maintainers will be happy to help in the slack channel #grafana-oncall: https://slack.grafana.com/
Your invite token: <TOKEN>, use it in the Grafana OnCall plugin.
```

3. If you started your container detached with -d check the log:
```bash
docker logs oncall-backend
```

### How to install "Grafana OnCall" Plugin and connect with a backend
1. Open Grafana in your browser and login as an Admin
2. Navigate to Configuration &rarr; Plugins
3. Type Grafana OnCall into the "Search Grafana plugins" field
4. Select the Grafana OnCall plugin and press the "Install" button
5. On the Grafana OnCall Plugin page Enable the plugin and go to the Configuration tab you should see a status field with the message
```
OnCall has not been setup, configure & initialize below.
```
6. Fill in configuration fields using the token you got from the backend earlier, then press "Install Configuration"
```
OnCall API URL: (The URL & port used to access OnCall)
http://host.docker.internal:8000

OnCall Invitation Token (Single use token to connect Grafana instance):
Invitation token from docker startup

Grafana URL (URL OnCall will use to talk to this Grafana instance):
http://localhost:3000  (or http://host.docker.internal:3000 if your grafana is running in Docker locally)
```

## Getting Help
- `#grafana-oncall` channel at https://slack.grafana.com/
- Grafana Labs community forum for OnCall: https://community.grafana.com
- File an [issue](https://github.com/grafana/oncall/issues) for bugs, issues and feature suggestions.

## Production Setup

Looking for the production instructions? We're going to release them soon. Please join our Slack channel to be the first to know about them. 

## Further Reading
- *Documentation* - [Grafana OnCall](https://grafana.com/docs/grafana-cloud/oncall/)
- *Blog Post* - [Announcing Grafana OnCall, the easiest way to do on-call management](https://grafana.com/blog/2021/11/09/announcing-grafana-oncall/)
- *Presentation* - [Deep dive into the Grafana, Prometheus, and Alertmanager stack for alerting and on-call management](https://grafana.com/go/observabilitycon/2021/alerting/?pg=blog)

## FAQ

- How do I generate a new invitation token to connect plugin with a backend?
```bash
docker exec oncall-backend python manage.py issue_invite_for_the_frontend --override
```
