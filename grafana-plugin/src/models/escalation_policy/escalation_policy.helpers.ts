import { pick } from 'lodash-es';

import { EscalationPolicy } from './escalation_policy.types';

export function prepareEscalationPolicy(value: EscalationPolicy) {
  return pick(value, ['step']);
}
