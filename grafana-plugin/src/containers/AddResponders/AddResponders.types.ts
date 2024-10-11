import { SelectableValue } from '@grafana/data';
import { ActionMeta } from '@grafana/ui';

import { ApiSchemas } from 'network/oncall-api/api.types';

export enum NotificationPolicyValue {
  Default = 0,
  Important = 1,
}

export type UserResponder = {
  data: ApiSchemas['UserIsCurrentlyOnCall'];
  important: boolean;
};
export type UserResponders = UserResponder[];

export type ResponderBaseProps = {
  onImportantChange: (value: SelectableValue<number>, actionMeta: ActionMeta) => void | {};
  handleDelete: React.MouseEventHandler<HTMLButtonElement>;
};
