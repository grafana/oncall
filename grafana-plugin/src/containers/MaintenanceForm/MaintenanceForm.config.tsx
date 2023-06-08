import React from 'react';

import { SelectableValue } from '@grafana/data';
import Emoji from 'react-emoji-render';

import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import { MaintenanceMode } from 'models/maintenance/maintenance.types';

export const form: { name: string; fields: FormItem[] } = {
  name: 'Maintenance',
  fields: [
    {
      name: 'alert_receive_channel_id',
      label: 'Integration',
      type: FormItemType.GSelect,
      validation: { required: true },
      extra: {
        modelName: 'alertReceiveChannelStore',
        displayField: 'verbal_name',
        valueField: 'id',
        showSearch: true,
        getOptionLabel: (item: SelectableValue) => <Emoji text={item?.label || ''} />,
      },
    },
    {
      name: 'mode',
      label: 'Mode',
      type: FormItemType.Select,
      validation: { required: true },
      normalize: (value) => value,
      extra: {
        options: [
          {
            value: MaintenanceMode.Debug,
            label: 'Debug (silence all escalations)',
          },
          {
            value: MaintenanceMode.Maintenance,
            label: 'Maintenance (collect everything in one alert group)',
          },
        ],
      },
    },
    {
      name: 'duration',
      label: 'Duration',
      type: FormItemType.Select,
      validation: { required: true },
      extra: {
        options: [
          {
            value: 3600,
            label: '1 hour',
          },
          {
            value: 10800,
            label: '3 hours',
          },
          {
            value: 21600,
            label: '6 hours',
          },
          {
            value: 43200,
            label: '12 hours',
          },
          {
            value: 86400,
            label: '24 hours',
          },
        ],
      },
    },
  ],
};
