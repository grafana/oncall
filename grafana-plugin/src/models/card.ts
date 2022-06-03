import { ReactElement } from 'react';

export interface CardData {
  title: string;
  subtitle?: string;
  value: number;
  icon: ReactElement;
  rate?: string;
  selectable?: boolean;
  selected?: boolean;
  id?: any;
  lg?: string;
  xl?: string;
}
