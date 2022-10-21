import moment from 'moment-timezone';

import { Maintenance } from './maintenance.types';

export const getMaintenanceProgress = (maintenance: Maintenance) => {
  const duration = maintenance.maintenance_till_timestamp - maintenance.started_at_timestamp;
  const passed = moment().unix() - maintenance.started_at_timestamp;

  return (passed / duration) * 100;
};
