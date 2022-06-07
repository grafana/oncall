export interface Cloud {
  id: string;
  username: string;
  email: string;
  cloud_data?: {
    status?: number;
    link?: string;
  };
}
