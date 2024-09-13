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

// IfEquals, WritableKeys, ReadonlyKeys based on https://stackoverflow.com/a/49579497/4931398
export type IfEquals<X, Y, A = X, B = never> = (<T>() => T extends X ? 1 : 2) extends <T>() => T extends Y ? 1 : 2
  ? A
  : B;

export type WritableKeys<T> = {
  [P in keyof T]-?: IfEquals<{ [Q in P]: T[P] }, { -readonly [Q in P]: T[P] }, P>;
}[keyof T];

export type ReadonlyKeys<T> = {
  [P in keyof T]-?: IfEquals<{ [Q in P]: T[P] }, { -readonly [Q in P]: T[P] }, never, P>;
}[keyof T];

export type OmitReadonlyMembers<T> = Omit<T, ReadonlyKeys<T>>;
