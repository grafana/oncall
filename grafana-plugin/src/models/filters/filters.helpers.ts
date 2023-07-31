export const getApiPathByPage = (page: string) => {
  return (
    {
      outgoing_webhooks: 'custom_buttons',
      incidents: 'alertgroups',
      integrations: 'alert_receive_channels',
    }[page] || page
  );
};
