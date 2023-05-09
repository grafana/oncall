import { FormItem, FormItemType } from 'components/GForm/GForm.types';

const Integration2HeartbeatForm: { name: string; fields: FormItem[] } = {
  name: 'Heartbeat',
  fields: [
    {
      name: 'alert_receive_channel',
      label: 'Setup heartbeat interval',
      description: 'OnCall will issue an alert group if no alert is received every',
      type: FormItemType.GSelect,
      validation: { required: true },
      extra: {
        showSearch: true,
      },
    },
    {
      name: 'endpoint',
      label: 'Endpoint',
      type: FormItemType.Input,
      extra: {
        disabled: true,
      },
    },
  ],
};

export default Integration2HeartbeatForm;
