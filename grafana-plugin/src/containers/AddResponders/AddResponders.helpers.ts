import { FormData } from 'components/ManualAlertGroup/ManualAlertGroup.config';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';

import { UserResponders } from './AddResponders.types';

export const prepareForUpdate = (selectedUsers: UserResponders, selectedTeam?: GrafanaTeam, data?: FormData) => ({
  ...(data || {}),
  team: selectedTeam ? selectedTeam.id : null,
  users: selectedUsers.map(({ important, data: { pk } }) => ({ important, id: pk })),
});
