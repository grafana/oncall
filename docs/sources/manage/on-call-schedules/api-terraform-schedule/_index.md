---
title: API & Terraform schedules
menuTitle: API & Terraform schedules
description: Learn how to use API and Terraform to manage on-call schedules.
weight: 100
keywords:
  - On-call
  - Schedules
  - Rotation
  - Calendar
  - Terraform
  - as-code
canonical: https://grafana.com/docs/oncall/latest/manage/on-call-schedules/api-terraform-schedules/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/manage/on-call-schedules/api-terraform-schedules/
  - /docs/grafana-cloud/alerting-and-irm/oncall/on-call-schedules/api-terraform-schedules/
---

# API & Terraform schedules

If your schedules became comprehensive, or you would like to distribute the same scheduling patterns through multiple
teams in the org, we suggest considering storing schedules as code.

- [Get started with Grafana OnCall and Terraform (blogpost)](https://grafana.com/blog/2022/08/29/get-started-with-grafana-oncall-and-terraform/)
- [Grafana Terraform provider reference (OnCall resources are managed using this provider)](https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/oncall_schedule)
- [OnCall API][oncall-api-reference]

{{% docs/reference %}}
[oncall-api-reference]: "/docs/oncall/ -> /docs/oncall/<ONCALL VERSION>/oncall-api-reference"
[oncall-api-reference]: "/docs/grafana-cloud/ -> /docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference"
{{% /docs/reference %}}
