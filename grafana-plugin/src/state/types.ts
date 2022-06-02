import { RootStore } from 'state/index';

export interface WithStoreProps {
  store: RootStore;
}

export interface SelectOption {
  value: string | number;
  display_name: string;
}
