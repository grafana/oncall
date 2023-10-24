export interface Label {
  id: string;
  name: string;
}

export interface LabelKey extends Label {}
export interface LabelValue extends Label {}

export interface LabelKeyValue {
  key: LabelKey;
  value: LabelValue;
}
