import { AppPluginMeta, KeyValue } from '@grafana/data';
import { useDrawer } from 'helpers/hooks';

import { RootStore } from 'state/rootStore';

export interface WithStoreProps {
  store: RootStore;
}

export interface WithDrawerConfig<T extends string> {
  drawerConfig: ReturnType<typeof useDrawer<T>>;
}

export interface PageProps<T extends KeyValue = KeyValue> {
  meta: AppPluginMeta<T>;
  query: KeyValue;
}

export interface SelectOption {
  value: string | number;
  display_name: string;
}
