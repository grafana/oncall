export interface Label {
  id: string;
  repr: string;
}

export interface LabelKey {
  id: string;
  repr: string;
}

export interface LabelValue {
  id: string;
  repr: string;
}

export interface LabelKeyValue {
  key: LabelKey;
  value: LabelValue;
}
