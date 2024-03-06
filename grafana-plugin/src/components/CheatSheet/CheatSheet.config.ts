export interface CheatSheetItem {
  name: string;
  listItems?: Array<{
    listItemName?: string;
    codeExample?: string;
  }>;
}

export interface CheatSheetInterface {
  name: string;
  description: string;
  fields: CheatSheetItem[];
}

export const groupingTemplateCheatSheet: CheatSheetInterface = {
  name: 'Grouping template cheatsheet',
  description:
    'Template is powered by Jinja2 and Markdown.\n Grouping template is used to extract key from the alert payload and group alerts based on that key. The key can combine different variables based on content and time. See examples below. ',
  fields: [
    {
      name: 'Additional variables and functions',
      listItems: [
        { listItemName: 'time(), datetimeformat, iso8601_to_time' },
        { listItemName: 'regex_replace, regex_match' },
      ],
    },
    {
      name: 'Examples',
      listItems: [
        { listItemName: 'group every hour', codeExample: '{{ time() | datetimeformat("%d-%m-%Y %H") }}' },
        { listItemName: 'group alerts every microsecond (every 0.000001 second)', codeExample: '{{ time() }}' },
        { listItemName: 'group based on the specific field', codeExample: '{{ payload.uuid }}' },
        { listItemName: 'group based on multiple fields', codeExample: '{{ payload.uuid }}-{{ payload.region }}' },
        {
          listItemName: 'group alerts with the same uuid, create new group every hour',
          codeExample: '{{ payload.uuid }}-{{ time() | datetimeformat("%d-%m-%Y %H") }}',
        },
      ],
    },
  ],
};

export const genericTemplateCheatSheet: CheatSheetInterface = {
  name: 'Web title template cheatsheet',
  description: 'Jinja2 is used for templating (docs). \n Markdown is used for markup',
  fields: [
    {
      name: 'Markdown refresher',
      listItems: [
        {
          codeExample: `**bold**, _italic_, >quote, \`code\`,
\`\`\`multiline code\`\`\`
<slug|url>
- bullet list`,
        },
      ],
    },
    {
      name: 'Jinja2 refresher ',
      listItems: [
        {
          listItemName: 'Extract field value',
          codeExample: '{{ payload.labels.foo }}',
        },
        {
          listItemName: 'Conditions',
          codeExample: `{%- if "status" in payload %}
  {{ payload.status }}
{% endif -%}`,
        },
        { listItemName: 'Booleans', codeExample: '{{ payload.status == "resolved" }}' },
        {
          listItemName: 'Loops',
          codeExample: `{% for label in labels %}
  {{ label.title }}
{% endfor %}`,
        },
      ],
    },
    {
      name: 'Additional jinja2 variables',
      listItems: [
        { listItemName: 'payload - payload of last alert in the group' },
        { listItemName: 'labels - labels assigned to the last alert in the group' },
        { listItemName: 'web_title, web_mesage, web_image_url - templates from Web' },
        { listItemName: 'payload, grafana_oncall_link, grafana_oncall_incident_id, integration_name, source_link' },
        { listItemName: 'time(), datetimeformat, datetimeformat_as_timezone, iso8601_to_time' },
        { listItemName: 'to_pretty_json' },
        { listItemName: 'regex_replace, regex_match' },
        { listItemName: 'b64decode' },
      ],
    },
    {
      name: 'Examples',
      listItems: [
        {
          listItemName: 'Show status if exists',
          codeExample: '{%- if "status" in payload %} \n **Status**: {{ payload.status }} \n {% endif -%}',
        },
        {
          listItemName: 'Check if field exists in payload, or labels, otherwise show “N/A” if neither exist',
          codeExample: '{{ payload.foo | labels.bar | default(“N/A”) }}',
        },
        {
          listItemName: 'Iterate over labels dictionary',
          codeExample: '**Labels:** \n {% for k, v in labels.items() %} \n *{{ k }}*: {{ v }} \n {% endfor %} ',
        },
      ],
    },
  ],
};

export const slackMessageTemplateCheatSheet: CheatSheetInterface = {
  name: 'Slack message template cheatsheet',
  description: 'Jinja2 is used for templating (docs). \n Markdown is used for markup',
  fields: [
    {
      name: 'Slack Markdown refresher',
      listItems: [
        { listItemName: '**bold**, _italic_, >quote, `code`, ```multiline code```,  <slug|url> - bullet list' },
      ],
    },
    {
      name: 'Jinja2 refresher ',
      listItems: [
        {
          listItemName: 'Extract field value',
          codeExample: '{{ payload.labels.foo }}',
        },
        {
          listItemName: 'Conditions',
          codeExample: '{%- if "status" in payload %} \n {{ payload.status }} \n {% endif -%}',
        },
        { listItemName: 'Booleans', codeExample: '{{ payload.status == “resolved” }}' },
        { listItemName: 'Loops', codeExample: '{% for label in labels %} \n {{ label.title }} \n {% endfor %}' },
      ],
    },
    {
      name: 'Additional jinja2 variables',
      listItems: [
        { listItemName: 'payload - payload of last alert in the group' },
        { listItemName: 'web_title, web_mesage, web_image_url - templates from Web' },
        { listItemName: 'payload, grafana_oncall_link, grafana_oncall_incident_id, integration_name, source_link' },
        { listItemName: 'time(), datetimeformat, iso8601_to_time' },
        { listItemName: 'to_pretty_json' },
        { listItemName: 'regex_replace, regex_match' },
      ],
    },
    {
      name: 'Examples',
      listItems: [
        {
          listItemName: 'Examples Convert Web template in Classic Markdown to Slack markdown',
          codeExample: `{{
    web_message
    | replace("**", "*")
    | regex_replace("/((.*))[(.*)]/", "<$2|$1>")
}}`,
        },
        {
          listItemName: 'Show status if exists',
          codeExample: `{%- if "status" in payload %}
**Status**: {{ payload.status }}
{% endif -%}`,
        },
        {
          listItemName: 'Show field value or “N/A” is not exist',
          codeExample: '{{ payload.labels.foo | default(“N/A”) }}',
        },
        {
          listItemName: 'Iterate over labels dictionary',
          codeExample: `**Labels:**
{% for k, v in payload["labels"].items() %}
*{{ k }}*: {{ v }}
{% endfor %}`,
        },
      ],
    },
  ],
};

export const alertGroupDynamicLabelCheatSheet: CheatSheetInterface = {
  name: 'Dynamic Label cheatsheet',
  description: 'Dynamic Label template is used to extract value for a specified key from the alert payload.',
  fields: [
    {
      name: 'Examples',
      listItems: [
        {
          listItemName:
            'Extracting the value associated with the "severity" key. If the key is not present, it defaults to "unknown."',
          codeExample: `{{ payload.get("severity", "unknown") }}`,
        },
      ],
    },
    {
      name: 'Jinja2 refresher ',
      listItems: [
        {
          listItemName: 'Extract field value',
          codeExample: '{{ payload.labels.foo }}',
        },
        {
          listItemName: 'Conditions',
          codeExample: '{%- if "status" in payload %} \n {{ payload.status }} \n {% endif -%}',
        },
        { listItemName: 'Booleans', codeExample: '{{ payload.status == “resolved” }}' },
        { listItemName: 'Loops', codeExample: '{% for label in labels %} \n {{ label.title }} \n {% endfor %}' },
      ],
    },
    {
      name: 'Additional jinja2 variables',
      listItems: [{ listItemName: 'payload - payload of the first alert in the group' }],
    },
  ],
};

export const alertGroupMultiLabelExtractionCheatSheet: CheatSheetInterface = {
  name: 'Multi-label extraction cheatsheet',
  description:
    'Multi-label extraction template allows extracting and modifying multiple labels from an alert payload. The Jinja template must result in string, representing valid JSON dictionary. See Examples for getting familiar with the idea',
  fields: [
    {
      name: 'Examples',
      listItems: [
        {
          listItemName: 'Extracting all the labels from the specific payload field',
          codeExample: `{{ payload.labels | tojson }}`,
        },
        {
          listItemName: 'Extract labels from different payload fields',
          codeExample: `{%- set labels = {} -%}
{# add several labels #}
{%- set labels = dict(labels, **payload.commonLabels) -%}
{# add one label #}
{%- set labels = dict(labels, **{"status": payload.status}) -%}
{# add label not from payload #}
{%- set labels = dict(labels, **{"service": "oncall"}) -%}
{# dump labels dict to json string, so OnCall can parse it #}
{{ labels | tojson }}
`,
        },
      ],
    },
    {
      name: 'Jinja2 refresher ',
      listItems: [
        { listItemName: 'Dump a structure to JSON string', codeExample: '{{ payload.labels | tojson }}' },
        {
          listItemName: 'Extract field value',
          codeExample: '{{ payload.labels.foo }}',
        },
        {
          listItemName: 'Conditions',
          codeExample: '{%- if "status" in payload %} \n {{ payload.status }} \n {% endif -%}',
        },
        { listItemName: 'Booleans', codeExample: '{{ payload.status == “resolved” }}' },
        { listItemName: 'Loops', codeExample: '{% for label in labels %} \n {{ label.title }} \n {% endfor %}' },
      ],
    },
    {
      name: 'Additional jinja2 variables',
      listItems: [{ listItemName: 'payload - payload of the first alert in the group' }],
    },
  ],
};

export const webhookPayloadCheatSheet: CheatSheetInterface = {
  name: 'Webhook Payload cheatsheet ',
  description:
    "Webhook payload template is powered by Jinja2. It's used to process webhook data and customize the output",
  fields: [
    {
      name: 'Examples',
      listItems: [
        {
          listItemName:
            'Construct a custom webhook payload from various webhook data fields and output it as a JSON string',
          codeExample: `{%- set payload = {} -%}
{# add alert group labels #}
{%- set payload = dict(payload, **{"labels": alert_group.labels}) -%}
{# add some other fields from webhook data just for example #}
{%- set payload = dict(payload, **{"event": event.type, "integration": integration.name}) -%}
{# encode payload dict to json #}
{{ payload | tojson }}
`,
        },
      ],
    },
    {
      name: 'Jinja2 refresher ',
      listItems: [
        {
          listItemName: 'Extract field value',
          codeExample: '{{ payload.labels.foo }}',
        },
        {
          listItemName: 'Show field value or “N/A” is not exist',
          codeExample: '{{ payload.labels.foo | default(“N/A”) }}',
        },
        {
          listItemName: 'Conditions',
          codeExample: '{%- if "status" in payload %} \n {{ payload.status }} \n {% endif -%}',
        },
        { listItemName: 'Booleans', codeExample: '{{ payload.status == “resolved” }}' },
        { listItemName: 'Loops', codeExample: '{% for label in labels %} \n {{ label.title }} \n {% endfor %}' },
        { listItemName: 'Dump a structure to JSON string', codeExample: '{{ payload.labels | tojson }}' },
      ],
    },
    {
      name: 'Additional jinja2 variables',
      listItems: [{ listItemName: 'payload - payload of the first alert in the group' }],
    },
  ],
};
