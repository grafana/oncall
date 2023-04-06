export const getApiPathByPage = (page: string) => {
  return (
    {
      outgoing_webhooks: 'custom_buttons',
      outgoing_webhooks_2: 'webhooks',
      incidents: 'alertgroups',
      integrations: 'alert_receive_channels',
    }[page] || page
  );
};
