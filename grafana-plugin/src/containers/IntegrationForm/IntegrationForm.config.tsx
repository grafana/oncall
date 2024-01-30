import React from 'react';

import { Icon, Label, Tooltip } from '@grafana/ui';

import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import { generateAssignToTeamInputDescription } from 'utils/consts';

export const form: { name: string; fields: FormItem[] } = {
  name: 'Integration',
  fields: [
    {
      label: 'Name',
      name: 'verbal_name',
      type: FormItemType.Input,
      placeholder: 'Integration Name',
      validation: { required: true },
    },
    {
      label: 'Description',
      name: 'description_short',
      type: FormItemType.TextArea,
      placeholder: 'Integration Description',
    },
    {
      name: 'team',
      label: (
        <Label>
          <span>Assign to team</span>&nbsp;
          <Tooltip content={generateAssignToTeamInputDescription('Integrations')} placement="right">
            <Icon name="info-circle" />
          </Tooltip>
        </Label>
      ),
      type: FormItemType.GSelect,
      extra: {
        modelName: 'grafanaTeamStore',
        displayField: 'name',
        valueField: 'id',
        showSearch: true,
        allowClear: true,
      },
    },
    {
      name: '', // this will skip field it in the submitted form
      label: 'Bi-directional Integration',
      type: FormItemType.PlainLabel,
      isHidden: (data) => data.integration !== 'servicenow',
    },
    {
      name: 'servicenow_url',
      label: 'Service Now URL',
      type: FormItemType.Input,
      isHidden: (data) => data.integration !== 'servicenow',
    },
    {
      name: 'authorization_header',
      label: 'Authorization Header',
      type: FormItemType.Input,
      isHidden: (data) => data.integration !== 'servicenow',
    },

    {
      name: 'alert_manager',
      type: FormItemType.Other,
    },
    {
      name: 'contact_point',
      type: FormItemType.Other,
    },
    {
      name: 'is_existing',
      type: FormItemType.Other,
    },
    {
      name: 'alerting',
      type: FormItemType.Other,
      render: true,
    },
  ],
};
