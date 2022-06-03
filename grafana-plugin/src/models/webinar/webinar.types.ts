import { UserDTO } from 'models/user';

export interface Webinar {
  id: string;
  title: string;
  additional_emails: string[];
  datetime: string;
  description: string;
  image: string;
  link: string;
  registered_users: Array<UserDTO['pk']>;
  subscribed: boolean;
}
