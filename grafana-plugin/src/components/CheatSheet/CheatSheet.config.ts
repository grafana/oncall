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
  description: 'Jinja2 is used for templating ( docs). ',
  fields: [
    {
      name: 'Additional variables and functions',
      listItems: [
        { listItemName: 'time(), datetimeformat, iso8601_to_time' },
        { listItemName: 'to_pretty_json' },
        { listItemName: 'regex_replace, regex_match' },
      ],
    },
    {
      name: 'Examples',
      listItems: [
        { listItemName: 'group every hour', codeExample: '{{ time() | datetimeformat("%d-%m-%Y %H") }}' },
        { listItemName: 'group every X hours', codeExample: '{{ every_hour(5) }}' },
        { listItemName: 'group alerts every microsecond (every 0.000001 second)', codeExample: '{{ time() }}' },
        { listItemName: 'group based on the specific field', codeExample: '{{ payload.uuid }}' },
        { listItemName: 'group based on multiple fields', codeExample: '{{ payload.uuid }} \n {{ payload.region }}' },
        {
          listItemName: 'group alerts with the same uuid, create new group every hour',
          codeExample: '{{ payload.uuid }} \n {{ time() | datetimeformat("%d-%m-%Y %H") }}',
        },
      ],
    },
  ],
};
