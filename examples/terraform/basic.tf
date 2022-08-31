terraform {
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = ">= 1.22.0"
    }
  }
}

provider "grafana" {
  alias               = "oncall"
  oncall_access_token = <YOUR_API_TOKEN>
}

data "grafana_oncall_user" "ikonstantinov" {
  provider = grafana.oncall
  username = "ikonstantinov"
}

resource "grafana_oncall_integration" "prod_alertmanager" {
  provider = grafana.oncall
  name     = "Prod AM"
  type     = "alertmanager"
  default_route {
    escalation_chain_id = grafana_oncall_escalation_chain.default.id
  }
}

resource "grafana_oncall_escalation_chain" "default" {
  provider = grafana.oncall
  name     = "default"
}

resource "grafana_oncall_escalation" "notify_me_step" {
  provider            = grafana.oncall
  escalation_chain_id = grafana_oncall_escalation_chain.default.id
  type                = "notify_persons"
  persons_to_notify   = [
    data.grafana_oncall_user.ikonstantinov.id
  ]
  position = 0
}