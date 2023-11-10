import { RenderedCell } from 'rc-table/lib/interface';

export interface TableColumn {
  width: any;
  title: string;
  key: string;
  render: (value: any, record: any, index: number) => React.ReactNode | RenderedCell<any>;
}
