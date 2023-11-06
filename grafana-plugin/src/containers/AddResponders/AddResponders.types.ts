import { SelectableValue } from '@grafana/data';
import { ActionMeta } from '@grafana/ui';

import { UserCurrentlyOnCall } from 'models/user/user.types';

export enum NotificationPolicyValue {
  Default = 0,
  Important = 1,
}

export type UserResponder = {
  data: UserCurrentlyOnCall;
  important: boolean;
};
export type UserResponders = UserResponder[];

export type ResponderBaseProps = {
  onImportantChange: (value: SelectableValue<number>, actionMeta: ActionMeta) => void | {};
  handleDelete: React.MouseEventHandler<HTMLButtonElement>;
};
