import { getColor, getOverrideColor } from 'models/schedule/schedule.helpers';

export const findColor = (shiftId, layers, overrides?) => {
  let color = undefined;

  const layerIndex = layers ? layers.findIndex((layer) => layer.shifts.some((shift) => shift.shiftId === shiftId)) : -1;

  const rotationIndex =
    layerIndex > -1 ? layers[layerIndex].shifts.findIndex((shift) => shift.shiftId === shiftId) : -1;

  if (layerIndex > -1 && rotationIndex > -1) {
    color = getColor(layerIndex, rotationIndex);
  } else if (overrides) {
    const overrideIndex = overrides ? overrides.findIndex((shift) => shift.shiftId === shiftId) : -1;

    if (overrideIndex > -1) {
      color = getOverrideColor(overrideIndex);
    }
  }

  return color;
};
