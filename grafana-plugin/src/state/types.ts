import { AppPluginMeta, KeyValue } from '@grafana/data';

import { RootStore } from 'state/index';

export interface WithStoreProps {
  store: RootStore;
}

export interface PageProps<T extends KeyValue = KeyValue> {
  meta: AppPluginMeta<T>;
  query: KeyValue;
}

export interface SelectOption {
  value: string | number;
  display_name: string;
}
