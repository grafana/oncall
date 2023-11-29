import { ApiSchemas } from 'network/oncall-api/api.types';

export interface LabelKeyValue {
  key: ApiSchemas['LabelKey'];
  value: ApiSchemas['LabelValue'];
}
