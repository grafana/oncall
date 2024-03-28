import { AppPluginMeta, KeyValue } from '@grafana/data';

import { RootStore } from 'state/rootStore';
import { useDrawer } from 'utils/hooks';

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
