export interface ItemRepresentation extends Record<string, string> {
}

export interface ItemGroup {
  key: ItemRepresentation;
  values: ItemRepresentation[];
}

export interface ItemSelected {
  key: ItemRepresentation;
  value: ItemRepresentation;
}