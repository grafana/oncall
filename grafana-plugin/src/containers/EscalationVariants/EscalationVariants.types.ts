import { SelectableValue } from '@grafana/data';
import { ActionMeta } from '@grafana/ui';

import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { User } from 'models/user/user.types';

export interface UserAvailability {
  warnings: Array<{ error: string; data: any }>;
}

export enum ResponderType {
  User,
  Team,
}

type Responder<DT> = {
  type: ResponderType;
  data: DT;
  important: boolean;
};

export type TeamResponder = Responder<GrafanaTeam>;
export type UserResponders = Array<Responder<User>>;
export type UserResponder = UserResponders[0];

export type ResponderBaseProps = {
  onImportantChange: (value: SelectableValue<number>, actionMeta: ActionMeta) => void | {};
  handleDelete: React.MouseEventHandler<HTMLButtonElement>;
};
