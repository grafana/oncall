export const WebhooksDefaultAlertGroup = {
  pk: '0',
  event: {
    type: 'resolve',
    time: '2023-04-19T21:59:21.714058+00:00',
  },
  user: {
    id: 'UVMX6YI9VY9PV',
    username: 'admin',
    email: 'admin@localhost',
  },
  alert_group: {
    id: 'I6HNZGUFG4K11',
    integration_id: 'CZ7URAT4V3QF2',
    route_id: 'RKHXJKVZYYVST',
    alerts_count: 1,
    state: 'resolved',
    created_at: '2023-04-19T21:53:48.231148Z',
    resolved_at: '2023-04-19T21:59:21.714058Z',
    acknowledged_at: '2023-04-19T21:54:39.029347Z',
    title: 'Incident',
    permalinks: {
      slack: null,
      telegram: null,
      web: 'https://**********.grafana.net/a/grafana-oncall-app/alert-groups/I6HNZGUFG4K11',
    },
  },
  alert_group_id: 'I6HNZGUFG4K11',
  alert_payload: {
    endsAt: '0001-01-01T00:00:00Z',
    labels: {
      region: 'eu-1',
      alertname: 'TestAlert',
    },
    status: 'firing',
    startsAt: '2018-12-25T15:47:47.377363608Z',
    annotations: {
      description: 'This alert was sent by user for the demonstration purposes',
    },
    generatorURL: '',
  },
  integration: {
    id: 'CZ7URAT4V3QF2',
    type: 'webhook',
    name: 'Main Integration - Webhook',
    team: 'Webhooks Demo',
  },
  notified_users: [],
  users_to_be_notified: [],
  responses: {
    WHP936BM1GPVHQ: {
      id: '7Qw7TbPmzppRnhLvK3AdkQ',
      created_at: '15:53:50',
      status: 'new',
      content: {
        message: 'Ticket created!',
        region: 'eu',
      },
    },
  },
};
