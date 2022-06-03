import { Alert } from 'models/alertgroup/alertgroup.types';
import { UserDTO } from 'models/user';

interface ResolutionNoteSource {
  id: number; // TODO check if string
  display_name: string;
}

export interface ResolutionNote {
  id: string;
  alert_group: Alert['pk'];
  created_at: string;
  source: ResolutionNoteSource;
  author: Partial<UserDTO>;
  text: string;
}

type ResolutionNoteSourceTypesOptions = {
  [key: number]: string;
};
export const ResolutionNoteSourceTypesToDisplayName: ResolutionNoteSourceTypesOptions = {
  0: 'slack',
  1: 'web',
};
