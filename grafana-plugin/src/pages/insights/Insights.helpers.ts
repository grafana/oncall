import { DataSourceRef } from '@grafana/schema';

export const getDataSource = (isOpenSource: boolean): DataSourceRef =>
  isOpenSource ? { uid: '$datasource' } : { uid: 'grafanacloud-usage' };
