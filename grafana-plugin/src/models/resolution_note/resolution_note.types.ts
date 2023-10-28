import { Alert } from 'models/alertgroup/alertgroup.types';
import { User } from 'models/user/user.types';

interface ResolutionNoteSource {
  id: number; // TODO check if string
  display_name: string;
}

export interface ResolutionNote {
  id: string;
  alert_group: Alert['pk'];
  created_at: string;
  source: ResolutionNoteSource;
  author: Partial<User>;
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
