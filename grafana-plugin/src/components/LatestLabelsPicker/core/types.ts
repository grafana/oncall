export interface ItemRepresentation {
  id: string;
  repr: string;
}

export interface ItemGroup {
  key: ItemRepresentation;
  values: ItemRepresentation[];
}

export interface ItemSelected {
  key: ItemRepresentation;
  value: ItemRepresentation;
}