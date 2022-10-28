import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';

export default [
  {
    id: 'K2E45EI2586HS',
    name: 'hook-1',
    team: null,
    webhook: 'http://google.ro',
    data: null,
    user: 'rares',
    password: 'password',
    authorization_header: 'auth-header',
    forward_whole_payload: false,
  },
  {
    id: 'KL3UZQQF2KE5V',
    name: 'hook-3',
    team: null,
    webhook: 'http://google.ro',
    data: null,
    user: null,
    password: null,
    authorization_header: null,
    forward_whole_payload: false,
  },
] as OutgoingWebhook[];
