import { RenderedCell } from 'rc-table/lib/interface';

export interface TableColumn {
  width?: string | number;
  title: string;
  key: string;
  render: (value: any, record: any, index: number) => React.ReactNode | RenderedCell<any>;
  className?: string;
  grow?: number;
}

export type KeysMatching<T extends object, V> = keyof {
  [K in keyof T as T[K] extends V ? K : never]: any;
};
