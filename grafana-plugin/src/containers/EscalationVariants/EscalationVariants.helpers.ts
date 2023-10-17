// TODO: move this type somewhere more centralized
import { FormData } from 'components/ManualAlertGroup/ManualAlertGroup.config';

import { TeamResponder, UserResponders } from './EscalationVariants.types';

export const prepareForUpdate = (selectedUsers: UserResponders, selectedTeam?: TeamResponder, data?: FormData) => ({
  ...(data || {}),
  team: selectedTeam ? { important: selectedTeam.important, id: selectedTeam.data.id } : null,
  users: selectedUsers.map(({ important, data: { pk } }) => ({ important, id: pk })),
});
