import { SelectableValue } from '@grafana/data';
import { UseFormGetValues } from 'react-hook-form';

import { AlertReceiveChannelStore } from 'models/alert_receive_channel/alert_receive_channel';
import { OnCallAGStatus } from 'utils/consts';

import { ServiceNowFormFields } from './ServiceNowStatusSection';

export class ServiceNowHelper {
  static getAvailableStatusOptions({
    getValues,
    currentAction,
    alertReceiveChannelStore,
  }: {
    currentAction: OnCallAGStatus;
    getValues: UseFormGetValues<ServiceNowFormFields>;
    alertReceiveChannelStore: AlertReceiveChannelStore;
  }): SelectableValue[] {
    const stateMapping = getValues()?.additional_settings?.state_mapping || {};
    const keys = Object.keys(stateMapping);

    // values are list of array-like values [label, id]
    const values = keys
      .map((k) => stateMapping[k])
      .filter(Boolean)
      .map((arr) => arr[1]);
    const statusList = (alertReceiveChannelStore.serviceNowStatusList || []).map(([name, id]) => ({ id, name }));

    return statusList
      .filter((status) => values.indexOf(status.id) === -1 || stateMapping?.[currentAction]?.[0] === status.name)
      .map((status) => ({
        value: status.id,
        label: status.name,
      }));
  }
}
