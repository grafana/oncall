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

// Users
data "grafana_oncall_user" "ikonstantinov" {
  provider = grafana.oncall
  username = "ikonstantinov"
}

data "grafana_oncall_user" "mkukuy" {
  provider = grafana.oncall
  username = "mkukuy"
}

// Schedule
resource "grafana_oncall_schedule" "primary" {
  provider  = grafana.oncall
  name      = "Primary"
  type      = "calendar"
  time_zone = "UTC"
  shifts    = [
    grafana_oncall_on_call_shift.week_shift.id
  ]
}

resource "grafana_oncall_on_call_shift" "week_shift" {
  provider      = grafana.oncall
  name          = "Week shift"
  type          = "rolling_users"
  start         = "2022-06-01T00:00:00"
  duration      = 60 * 60 * 24 // 24 hours
  frequency     = "weekly"
  by_day        = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
  week_start    = "MO"
  rolling_users = [
    [data.grafana_oncall_user.ikonstantinov.id],
    [data.grafana_oncall_user.mkukuy.id]
  ]
  time_zone = "UTC"
}

// Prod Alertmanager Integration
resource "grafana_oncall_integration" "prod_alertmanager" {
  provider = grafana.oncall
  name     = "Prod AM"
  type     = "alertmanager"
  default_route {
    escalation_chain_id = grafana_oncall_escalation_chain.default.id
  }
}

// Default escalation chain
resource "grafana_oncall_escalation_chain" "default" {
  provider = grafana.oncall
  name     = "default"
}

resource "grafana_oncall_escalation" "notify_schedule" {
  provider                     = grafana.oncall
  escalation_chain_id          = grafana_oncall_escalation_chain.default.id
  type                         = "notify_on_call_from_schedule"
  notify_on_call_from_schedule = grafana_oncall_schedule.primary.id
  position                     = 0
}