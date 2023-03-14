export const getApiPathByPage = (page: string) => {
  return { outgoing_webhooks: 'custom_buttons', incidents: 'alertgroups' }[page] || page;
};
