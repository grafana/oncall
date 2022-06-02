import { User } from 'models/user/user.types';

export interface OrganizationLog {
  id: string;
  author: Partial<User>;
  type: number;
  created_at: string;
  description: string;
  labels: string[];
}
