import React, { useEffect, useReducer } from 'react';

import { SelectableValue } from '@grafana/data';
import { HorizontalGroup, Select, SelectBaseProps, VerticalGroup } from '@grafana/ui';
import { observer } from 'mobx-react';
import { Controller, useFormContext } from 'react-hook-form';

import { Text } from 'components/Text/Text';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useCurrentIntegration } from 'pages/integration/OutgoingTab/OutgoingTab.hooks';
import { useStore } from 'state/useStore';
import { OnCallAGStatus } from 'utils/consts';

import { ServiceNowHelper } from './ServiceNowConfig.helpers';

export interface ServiceNowStatusMapping {
  [OnCallAGStatus.Firing]?: string;
  [OnCallAGStatus.Resolved]?: string;
  [OnCallAGStatus.Silenced]?: string;
  [OnCallAGStatus.Acknowledged]?: string;
}

export interface ServiceNowFormFields {
  additional_settings: ApiSchemas['AlertReceiveChannel']['additional_settings'];
}

export const ServiceNowStatusSection: React.FC = observer(() => {
  const { control, setValue, getValues } = useFormContext<ServiceNowFormFields>();

  const [, forceUpdate] = useReducer((x) => x + 1, 0);

  const { alertReceiveChannelStore } = useStore();
  const currentIntegration = useCurrentIntegration();
  const { id } = currentIntegration;

  useEffect(() => {
    (async () => {
      await alertReceiveChannelStore.fetchServiceNowStatusList({ id });
      forceUpdate();
    })();
  }, []);

  const selectCommonProps: Partial<SelectBaseProps<any>> = {
    backspaceRemovesValue: true,
    isClearable: true,
    placeholder: 'Not Selected',
  };

  return (
    <VerticalGroup spacing="md">
      <HorizontalGroup spacing="xs" align="center">
        <Text type="primary" strong>
          Status Mapping
        </Text>
      </HorizontalGroup>

      <table className={'filter-table'}>
        <thead>
          <tr>
            <th>
              <Text type="primary">OnCall Alert group status</Text>
            </th>
            <th>
              <Text type="primary">ServiceNow incident status</Text>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Firing</td>

            <td>
              <Controller
                name={'additional_settings.state_mapping.firing'}
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    value={field.value?.[1]}
                    key="state_mapping.firing"
                    menuShouldPortal
                    className="select control"
                    options={ServiceNowHelper.getAvailableStatusOptions({
                      getValues,
                      currentAction: OnCallAGStatus.Firing,
                      alertReceiveChannelStore,
                    })}
                    onChange={(option: SelectableValue) => {
                      setValue(
                        'additional_settings.state_mapping.firing',
                        option ? [option.label, option.value] : null
                      );
                      forceUpdate();
                    }}
                    {...selectCommonProps}
                  />
                )}
              />
            </td>
          </tr>

          <tr>
            <td>Acknowledged</td>

            <td>
              <Controller
                name={'additional_settings.state_mapping.acknowledged'}
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    value={field.value?.[1]}
                    defaultValue={field.value?.[1]}
                    menuShouldPortal
                    className="select control"
                    disabled={false}
                    options={ServiceNowHelper.getAvailableStatusOptions({
                      getValues,
                      currentAction: OnCallAGStatus.Acknowledged,
                      alertReceiveChannelStore,
                    })}
                    onChange={(option: SelectableValue) => {
                      setValue(
                        'additional_settings.state_mapping.acknowledged',
                        option ? [option.label, option.value] : null
                      );
                      forceUpdate();
                    }}
                    {...selectCommonProps}
                  />
                )}
              />
            </td>
          </tr>

          <tr>
            <td>Resolved</td>
            <td>
              <Controller
                name={'additional_settings.state_mapping.resolved'}
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    value={field.value?.[1]}
                    defaultValue={field.value?.[1]}
                    menuShouldPortal
                    className="select control"
                    disabled={false}
                    options={ServiceNowHelper.getAvailableStatusOptions({
                      getValues,
                      currentAction: OnCallAGStatus.Resolved,
                      alertReceiveChannelStore,
                    })}
                    onChange={(option: SelectableValue) => {
                      setValue(
                        'additional_settings.state_mapping.resolved',
                        option ? [option.label, option.value] : null
                      );
                      forceUpdate();
                    }}
                    {...selectCommonProps}
                  />
                )}
              />
            </td>
          </tr>

          <tr>
            <td>Silenced</td>
            <td>
              <Controller
                name={'additional_settings.state_mapping.silenced'}
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    value={field.value?.[1]}
                    menuShouldPortal
                    className="select control"
                    disabled={false}
                    options={ServiceNowHelper.getAvailableStatusOptions({
                      getValues,
                      currentAction: OnCallAGStatus.Silenced,
                      alertReceiveChannelStore,
                    })}
                    onChange={(option: SelectableValue) => {
                      setValue(
                        'additional_settings.state_mapping.silenced',
                        option ? [option.label, option.value] : null
                      );
                      forceUpdate();
                    }}
                    {...selectCommonProps}
                  />
                )}
              />
            </td>
          </tr>
        </tbody>
      </table>
    </VerticalGroup>
  );
});
