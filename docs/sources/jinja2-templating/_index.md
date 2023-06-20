---
canonical: https://grafana.com/docs/oncall/latest/jinja2-templating/
title: Jinja2 templating
weight: 1000
---

## Jinja2 templating

Grafana OnCall can integrate with any monitoring systems that can send alerts using
webhooks with JSON payloads. By default, webhooks deliver raw JSON payloads. When Grafana
OnCall receives an alert and parses its payload, a default pre-configured alert template
is applied to modify the alert payload to be more human-readable. These alert templates
are customizable for any integration. Templates are also used to notify different
escalation chains based on the content of the alert payload.

<iframe width="560" height="315" src="https://www.youtube.com/embed/S6Is8hhyCos" title="YouTube video player"
frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture;
web-share" allowfullscreen></iframe>

## Alert payload

Alerts received by Grafana OnCall contain metadata as keys and values in a JSON object.
The following is an example of an alert received by Grafana OnCall initiated by Grafana
Alerting:

```json
{
  "dashboardId": 1,
  "title": "[Alerting] Panel Title alert",
  "message": "Notification Message",
  "evalMatches": [
    {
      "value": 1,
      "metric": "Count",
      "tags": {}
    }
  ],
  "imageUrl": "https://grafana.com/static/assets/img/blog/mixed_styles.png",
  "orgId": 1,
  "panelId": 2,
  "ruleId": 1,
  "ruleName": "Panel Title alert",
  "ruleUrl": "http://localhost:3000/d/hZ7BuVbWz/test-dashboard?fullscreen\u0026edit\u0026tab=alert\u0026panelId=2\u0026orgId=1",
  "state": "alerting",
  "tags": {
    "tag name": "tag value"
  }
}
```

In Grafana OnCall every alert and alert group have the following fields:

- `Title`, `Message` and `Image Url` for each notification method (Web, Slack, Ms Teams, SMS, Phone, Email, etc.)
- `Grouping Id` - unique identifier for each non-resolved alert group
- `Resolved by source`
- `Acknowledged by source`
- `Source link`

The JSON payload is converted to OnCall fields. For example:

- `{{ payload.title }}` -> `Title`
- `{{ payload.message }}` -> `Message`
- `{{ payload.imageUrl }}` -> `Image Url`

The result is that each field of the alert in OnCall is now mapped to the JSON payload
keys. This also true for the
alert behavior:

- `{{ payload.ruleId }}` -> Grouping Id
- `{{ 1 if payload.state == 'OK' else 0 }}` -> Resolve Signal

Grafana OnCall provides a pre configured default Jinja template for supported
integrations. If your monitoring system is
not in the Grafana OnCall integrations list, you can create a generic `webhook`
integration, send an alert, and configure
your templates.

## Types of templates

Alert templates allow you to format any alert fields recognized by Grafana OnCall. You can
customize default alert
templates for all the different ways you receive your alerts such as web, slack, SMS, and
email. For more advanced
customization, use Jinja templates.

### Routing template

- `Routing Template` - used to route alerts to different escalation chains based on alert content (Conditional template, output should be `True`)

   > **Note:** For conditional templates, the output should be `True` to be applied, for example `{{ True if payload.state == 'OK' else False }}`

#### Appearance templates

How alerts displayed in the UI, messengers and notifications

- `Title`, `Message`, `Image url` for Web
- `Title`, `Message`, `Image url` for Slack
- `Title`, `Message`, `Image url` for MS Teams
- `Title`, `Message`, `Image url` for Telegram
- `Title` for SMS
- `Title` for Phone Call
- `Title`, `Message` for Email

#### Behavioral templates

- `Grouping Id` - applied to every incoming alert payload after the `Routing Template`. It
can be based on time, or alert content, or both. If the resulting grouping id matches an
existing non-resolved alert group grouping id, the alert will be grouped accordingly.
Otherwise, a new alert group will be created
- `Autoresolution` - used to auto-resolve alert groups with status `Resolved by source`
(Conditional template, output should be `True`)
- `Auto acknowledge` - used to auto-acknowledge alert groups with status `Acknowledged by
source` (Conditional template, output should be `True`)
- `Source link` - Used to customize the URL link to provide as the "source" of the alert.

   > **Note:** For conditional templates, the output should be `True` to be applied, for
   example `{{ True if payload.state == 'OK' else False }}`

> **Pro Tip:** As a best practice, add _Playbooks_, _Useful links_, or _Checklists_ to the
alert message.

#### How to edit templates

1. Open **Integration** page for the integration you want to edit
1`. Click **Edit** button for the Templates Section. Now you can see previews of all
templates for the Integration
1. Select the template you want to edit and click **Edit** button right to the template
name. Template editor will be opened. First column is the example alert payload, second
column is the Template itself, and third column is used to view rendered result.
1. Select one of the **Recent Alert groups** for the integration to see it's `latest alert
payload`. If you want to edit this payload, click **Edit** button right to the Alert Group
Name.
1. Alternatively, you can click **Use custom payload** and write your own payload to see
how it will be rendered
1. Press `Control + Enter` in the editor to see suggestions
1. Click **Cheatsheet** in the second column to get some inspiration.
1. If you edit Messenger templates, click **Save and open Alert Group in ChatOps** to see
how the alert will be rendered in the messenger right in the messenger (Only works for
Alert Group that exists in the messenger)
1. Click **Save** to save the templat

## Advanced Jinja templates

Grafana OnCall uses [Jinja templating language](http://jinja.pocoo.org/docs/2.10/) to
format alert groups for the Web,
Slack, phone calls, SMS messages, and more because the JSON format is not easily readable
by humans. As a result, you
can decide what you want to see when an alert group is triggered as well as how it should
be presented.

Jinja2 offers simple but multi-faceted functionality by using loops, conditions,
functions, and more.

> **NOTE:** Every alert from a monitoring system comes in the key/value format.

Grafana OnCall has rules about which of the keys match to: `__title`, `message`, `image`, `grouping`, and `auto-resolve__`.

### Loops

Monitoring systems can send an array of values. In this example, you can use Jinja to
iterate and format the alert
using a Grafana example:

```.jinja2
*Values:*
 {% for evalMatch in payload.evalMatches -%}
 `{{ evalMatch['metric'] }}: '{{ evalMatch['value'] -}}'`{{ " " }}
 {%- endfor %}
```

### Conditions

You can add instructions if an alert comes from a specified Grafana alert rule:

````jinja2
{% if  payload.ruleId == '1' -%}
*Alert TODOs*
1. Get acess to the container
    ```
        kubectl port-forward service/example 3000:80
    ```
2. Check for the exception.
3. Open the container and reload caches.
4. Click Custom Button `Send to Jira`
{%- endif -%}
````

### Built-in Jinja functions

Jinja2 includes built-in functions that can also be used in Grafana OnCall. For example:

```.jinja2
{{ payload | tojson_pretty }}
```

Built-in functions:

- `abs`
- `capitalize`
- `trim`
- You can see the full list of Jinja built-in functions on github [here](https://github.com/pallets/jinja/blob/3915eb5c2a7e2e4d49ebdf0ecb167ea9c21c60b2/src/jinja2/filters.py#L1307)

### Functions added by Grafana OnCall

- `time` - current time
- `tojson_pretty` - JSON prettified
- `iso8601_to_time` - converts time from iso8601 (`2015-02-17T18:30:20.000Z`) to datetime
- `datetimeformat` - converts time from datetime to the given format (`%H:%M / %d-%m-%Y` by default)
- `regex_replace` - performs a regex find and replace
- `regex_match` - performs a regex match, returns `True` or `False`. Usage example: `{{ payload.ruleName | regex_match(".*") }}`

{{< section >}}
