export interface Item {
  key: string;
  type: string;
  data: ItemData;
  item?: string;
}

export interface ItemData {
  name: string;
  desc?: string;
}
