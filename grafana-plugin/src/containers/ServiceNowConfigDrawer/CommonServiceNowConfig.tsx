import React from 'react';

import { SelectableValue } from '@grafana/data';
import { HorizontalGroup, Icon, Select, SelectBaseProps, VerticalGroup } from '@grafana/ui';
import { Controller, useFormContext } from 'react-hook-form';

import { Text } from 'components/Text/Text';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';
import { OnCallAGStatus } from 'utils/consts';

export interface ServiceNowStatusMapping {
  [OnCallAGStatus.Firing]?: string;
  [OnCallAGStatus.Resolved]?: string;
  [OnCallAGStatus.Silenced]?: string;
  [OnCallAGStatus.Acknowledged]?: string;
}

interface ServiceNowFormFields {
  additional_settings: ApiSchemas['AlertReceiveChannel']['additional_settings'];
}

interface CommonServiceNowConfigProps {
  statusMapping: ServiceNowStatusMapping;
  setStatusMapping: React.Dispatch<React.SetStateAction<ServiceNowStatusMapping>>;
}

export const CommonServiceNowConfig: React.FC<CommonServiceNowConfigProps> = ({ statusMapping, setStatusMapping }) => {
  const { control, setValue } = useFormContext<ServiceNowFormFields>();
  const { alertReceiveChannelStore } = useStore();

  const selectCommonProps: Partial<SelectBaseProps<any>> = {
    backspaceRemovesValue: true,
    isClearable: true,
    placeholder: 'Not Selected',
  };

  return (
    <VerticalGroup spacing="md">
      <HorizontalGroup spacing="xs" align="center">
        <Text type="primary" size="small">
          Status Mapping
        </Text>
        <Icon name="info-circle" />
      </HorizontalGroup>

      <table className={'filter-table'}>
        <thead>
          <tr>
            <th>OnCall Alert group status</th>
            <th>ServiceNow incident status</th>
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
                    key="state_mapping.firing"
                    menuShouldPortal
                    className="select control"
                    options={getAvailableStatusOptions(OnCallAGStatus.Firing)}
                    onChange={(option: SelectableValue) => {
                      onStatusSelectChange(option, OnCallAGStatus.Firing);
                      setValue('additional_settings.state_mapping.firing', null);
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
                    menuShouldPortal
                    className="select control"
                    disabled={false}
                    options={getAvailableStatusOptions(OnCallAGStatus.Acknowledged)}
                    onChange={(option: SelectableValue) => {
                      onStatusSelectChange(option, OnCallAGStatus.Acknowledged);
                      setValue('additional_settings.state_mapping.acknowledged', null);
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
                    menuShouldPortal
                    className="select control"
                    disabled={false}
                    options={getAvailableStatusOptions(OnCallAGStatus.Resolved)}
                    onChange={(option: SelectableValue) => {
                      onStatusSelectChange(option, OnCallAGStatus.Resolved);
                      setValue('additional_settings.state_mapping.resolved', null);
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
                    menuShouldPortal
                    className="select control"
                    disabled={false}
                    options={getAvailableStatusOptions(OnCallAGStatus.Silenced)}
                    onChange={(option: SelectableValue) => {
                      onStatusSelectChange(option, OnCallAGStatus.Silenced);
                      setValue('additional_settings.state_mapping.silenced', null);
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

  function onStatusSelectChange(option: SelectableValue, action: OnCallAGStatus) {
    setStatusMapping({
      ...statusMapping,
      [action]: option?.label,
    });
  }

  function getAvailableStatusOptions(currentAction: OnCallAGStatus) {
    const keys = Object.keys(statusMapping);
    const values = keys.map((k) => statusMapping[k]).filter(Boolean);

    return (alertReceiveChannelStore.serviceNowStatusList || [])
      .filter((status) => values.indexOf(status.name) === -1 || statusMapping[currentAction] === status.name)
      .map((status) => ({
        value: status.id,
        label: status.name,
      }));
  }
};