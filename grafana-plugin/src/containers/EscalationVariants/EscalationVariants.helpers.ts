import { User } from 'models/user/user.types';

import { ResponderType } from './EscalationVariants.types';

export const deduplicate = (value) => {
  const deduplicatedUserResponders = [];
  value.userResponders.forEach((userResponder) => {
    if (!deduplicatedUserResponders.some((responder) => responder.data.pk === userResponder.data.pk)) {
      deduplicatedUserResponders.push(userResponder);
    }
  });

  const deduplicatedScheduleResponders = [];
  value.scheduleResponders.forEach((scheduleResponder) => {
    if (!deduplicatedScheduleResponders.some((responder) => responder.data.id === scheduleResponder.data.id)) {
      deduplicatedScheduleResponders.push(scheduleResponder);
    }
  });

  return {
    ...value,
    scheduleResponders: deduplicatedScheduleResponders,
    userResponders: deduplicatedUserResponders,
  };
};

export function prepareForUpdate(userResponders, scheduleResponders, data?) {
  return {
    ...data,
    users: userResponders.map((userResponder) => ({ important: userResponder.important, id: userResponder.data.pk })),
    schedules: scheduleResponders.map((scheduleResponder) => ({
      important: scheduleResponder.important,
      id: scheduleResponder.data.id,
    })),
  };
}

export function prepareForEdit(userResponders) {
  return {
    userResponders: (userResponders || []).map(({ pk }: { pk: User['pk'] }) => ({
      type: ResponderType.User,
      data: { pk },
      important: false,
    })),
    scheduleResponders: [],
  };
}
