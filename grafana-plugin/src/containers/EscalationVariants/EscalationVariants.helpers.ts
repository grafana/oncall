// TODO: move this type somewhere more centralized
import { FormData } from 'components/ManualAlertGroup/ManualAlertGroup.config';

import { TeamResponder, UserResponders } from './EscalationVariants.types';

export const prepareForUpdate = (selectedTeam: TeamResponder, selectedUsers: UserResponders, data: FormData) => ({
  ...data,
  team: selectedTeam === undefined ? null : { important: selectedTeam.important, id: selectedTeam.data.id },
  users: selectedUsers.map(({ important, data: { pk } }) => ({ important, id: pk })),
});

export const prepareForEdit = (_selectedUsers: UserResponders) => ({
  // users: (selectedUsers || []).map(({ pk }: { pk: User['pk'] }) => ({
  //   type: ResponderType.User,
  //   data: { pk },
  //   important: false,
  // })),
  users: [],
  // TODO:
  team: null,
});
