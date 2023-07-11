import { allTimezones } from './timezone.helpers';

export type Timezone = (typeof allTimezones)[number];
