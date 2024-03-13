import { ApiSchemas } from 'network/oncall-api/api.types';

export function prepareForEdit(item: ApiSchemas['AlertReceiveChannel']): Partial<ApiSchemas['AlertReceiveChannel']> {
  return {
    verbal_name: item.verbal_name,
    description_short: item.description_short,
    team: item.team,
    labels: item.labels,
    integration: item.integration,

    additional_settings: {
      ...item.additional_settings,
    },
  };
}
