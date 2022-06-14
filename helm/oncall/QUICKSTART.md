Quick Start 

Cluster requirements:
* ensure you can run x86-64/amd64 workloads. arm64 architecture is currently not supported


NOTE:

Default chart places the stateful services into the current installation into the cluster. 
This services are provided for the convenience and are not intended for production. 
They need to be properly managed, maintained and backed up.
We recommend to run stateful applications, such as MySql and RabbitMQ separately or use managed solutions
as grafana does in Grafana Cloud.
https://gitlab.com/gitlab-org/charts/gitlab/-/blob/master/doc/installation/index.md

Prerequisites:
Tools:
* kubectl v1.22
* helm v3

Infrastructure:
* kubernetes cluster. Recomended resources: X vcpu and Y Gb of RAM 
Stateful services are recommended outside of the cluster using managed solutions or compute nodes
 1. MySQL 5.7 database
We recommend using 
 2. Rabbitmq



1. Prepare the chart values

2. Install the chart

3. Finish the configuration

3.1. Get the external ip address

3.2. Set up the DNS
The external IP that is allocated to the ingress-controller is the IP to which all incoming traffic should be routed. To enable this, add it to a DNS zone you control, for example as www.example.com.
This quick-start assumes you know how to assign a DNS entry to an IP address and will do so.

3.3. Open Grafana and connect Grafana OnCall plugin to Grafana OnCall Backend


Troubleshooting:
Error: failed post-install: warning: Hook post-install oncall/templates/cert-issuer.yaml failed: Internal error occurred: failed calling webhook "webhook.cert-manager.io": failed to call webhook: Post "https://oncall-ildar-cert-manager-webhook.default.svc:443/mutate?timeout=30s": no endpoints available for service "oncall-ildar-cert-manager-webhook"
Upgrade the release

Error: failed post-install: warning: Hook post-install oncall/templates/cert-issuer.yaml failed: Internal error occurred: failed calling webhook "webhook.cert-manager.io": failed to call webhook: Post "https://oncall-ildar-cert-manager-webhook.default.svc:443/mutate?timeout=30s": no endpoints available for service "oncall-ildar-cert-manager-webhook"

