import { pick } from 'lodash-es';

import { EscalationPolicy } from './escalation_policy.types';

export const prepareEscalationPolicy = (value: EscalationPolicy) => pick(value, ['step']);
