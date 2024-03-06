import { ApiSchemas } from 'network/oncall-api/api.types';

interface ResolutionNoteSource {
  id: number; // TODO check if string
  display_name: string;
}

export interface ResolutionNote {
  id: string;
  alert_group: ApiSchemas['AlertGroup']['pk'];
  created_at: string;
  source: ResolutionNoteSource;
  author: Partial<ApiSchemas['User']>;
  text: string;
}

type ResolutionNoteSourceTypesOptions = {
  [key: number]: string;
};
export const ResolutionNoteSourceTypesToDisplayName: ResolutionNoteSourceTypesOptions = {
  0: 'Slack',
  1: 'Web',
  2: 'Mobile App',
};
