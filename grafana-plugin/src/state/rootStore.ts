/*
 * Important!
   Make sure import of plugin/dayjs is placed in a proper location
   Otherwise the dayjs extenders won't be called and the dayjs functionality will be altered, thus leading to all sort of bugs
 */

import 'plugin/dayjs';

import { RootBaseStore } from './rootBaseStore/RootBaseStore';

export class RootStore extends RootBaseStore {}

export const rootStore = new RootStore();
