# Contribute the new Integration to OnCall

Related: [DEVELOPER.md](../../dev/README.md)

"Integration" in OnCall is a pre-configured webhook for alert consumption from alert sources. Usually, alert sources
are monitoring systems such as Grafana or Zabbix.

Integration is a set of "templates" which are dumped from the integration config once the integration is created.
Further changes to "templates" don't reflect on the integration config. Read more about templates
[here](https://grafana.com/docs/oncall/latest/integrations/create-custom-templates/).

This instruction is supposed to help you to build templates to integrate OnCall with a new source of alerts. If you
don't want to contribute to OnCall and are looking for a help integrating with custom alert source as a user,
refer to [this](https://grafana.com/docs/oncall/latest/integrations/create-custom-templates/) instruction.

## Files related to Integrations

0. Refer to "Grafana" integration as the most complete example.
1. Each integration should have a `{{integration_name_in_snake_case}}.py` file in `/engine/config_integrations`.
   There you'll find Templates that will be copied to the Integration Templates once the integration is created by the
   user in the OnCall UI; Example Payload; and Tests which should match the result of the rendering of Example Payload
   as using Templates. The best way to build such a file is to create Webhook Integration, write & debug templates in
   the UI first and copy-paste them to the file after.
2. Each integration should be listed in the `/engine/settings/base.py` file, section `INSTALLED_ONCALL_INTEGRATIONS`.
3. Each integration should have "How to connect" instruction stored as `integration_{{integration_name_in_snake_case}}.html`
   in the `engine/apps/integrations/html` folder. `.py` file has a `slug` field that is used to locate `.html` file.

## What do we expect from high-quality integration?

1. User-friendly integration instruction.
2. Proper grouping following source's logics. If source generates multiple alerts per "detection" it would be nice to
   provide suitable grouping & resolving configuration in the templates.
3. Awesome rendering. We all love when alerts look good in Slack, SMS and all other rendering destinations.
