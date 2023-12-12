import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';

const countNumberOfInheritedAndCustomLabels = (alert_group_labels: AlertReceiveChannel['alert_group_labels']) => {
  const inheritedCount = alert_group_labels.inheritable
    ? Object.keys(alert_group_labels.inheritable).filter((labelKey) => alert_group_labels.inheritable?.[labelKey])
        .length
    : 0;
  const customCount = alert_group_labels.custom?.length || 0;
  return inheritedCount + customCount;
};

export const getIsTooManyLabelsWarningVisible = (
  alert_group_labels: AlertReceiveChannel['alert_group_labels'],
  limit = 15
) => countNumberOfInheritedAndCustomLabels(alert_group_labels) > limit;

export const getIsAddBtnDisabled = ({ custom }: AlertReceiveChannel['alert_group_labels']) => {
  const lastItem = custom.at(-1);
  return lastItem && (lastItem?.key.id === undefined || lastItem?.value.id === undefined);
};
