import { RenderedCell } from 'rc-table/lib/interface';

export interface TableColumn {
  width?: string | number;
  title: string;
  key: string;
  render: (value: any, record: any, index: number) => React.ReactNode | RenderedCell<any>;
  className?: string;
  grow?: number;
}

export type PropertiesThatExtendsAnotherClass<OriginalObj, AnotherClass> = keyof {
  [Prop in keyof OriginalObj as OriginalObj[Prop] extends AnotherClass ? Prop : never]: unknown;
};
