import { FormItem, FormItemType } from 'components/GForm/GForm.types';
import { generateAssignToTeamInputDescription } from 'utils/consts';

import { IntegrationFormFieldName } from './IntegrationForm.types';

export const form: { name: string; fields: FormItem[] } = {
  name: 'Integration',
  fields: [
    {
      label: 'Name',
      name: IntegrationFormFieldName.VerbalName,
      type: FormItemType.Input,
      placeholder: 'Integration Name',
      validation: { required: true },
    },
    {
      label: 'Description',
      name: IntegrationFormFieldName.DescriptionShort,
      type: FormItemType.TextArea,
      placeholder: 'Integration Description',
    },
    {
      label: 'Assign to team',
      name: IntegrationFormFieldName.Team,
      description: generateAssignToTeamInputDescription('Integrations'),
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
      name: IntegrationFormFieldName.Alerting,
      type: FormItemType.Other,
      render: true,
    },
    {
      name: IntegrationFormFieldName.AlertManager,
      type: FormItemType.Other,
    },
    {
      name: IntegrationFormFieldName.ContactPoint,
      type: FormItemType.Other,
    },
    {
      name: IntegrationFormFieldName.IsExisting,
      type: FormItemType.Other,
    },
    {
      name: IntegrationFormFieldName.Labels,
      type: FormItemType.Other,
      render: true,
    },
  ],
};
