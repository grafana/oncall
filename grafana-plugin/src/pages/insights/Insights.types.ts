import { DataSourceRef } from '@grafana/schema';

export interface InsightsConfig {
  isOpenSource: boolean;
  datasource: DataSourceRef;
  stack: string;
}
