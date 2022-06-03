export interface GlobalSetting {
  id: string;
  name: string;
  description: string;
  default_value: any;
  value: any;
  is_secret: boolean;
  error: string;
}
