import { SHIFT_SWAP_COLOR } from 'models/schedule/schedule.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';

export const getTitle = (user: ApiSchemas['User']) => {
  return user ? user.username.split(' ')[0] : null;
};

export const getScheduleSlotStyleParams = (baseColor: string, isShiftSwap: boolean, hasBenefactor: boolean) => {
  let color = baseColor;
  let backgroundColor = color;
  let border = undefined;
  let textColor = '#fff';
  if (isShiftSwap) {
    backgroundColor = SHIFT_SWAP_COLOR;
    if (!hasBenefactor) {
      color = SHIFT_SWAP_COLOR;
      backgroundColor = 'transparent';
      border = `1px solid ${SHIFT_SWAP_COLOR}`;
      textColor = SHIFT_SWAP_COLOR;
    }
  }

  return { color, backgroundColor, border, textColor };
};
