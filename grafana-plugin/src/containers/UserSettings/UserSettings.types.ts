import { User, UserRole } from 'models/user/user.types';

export enum UserSettingsTab {
  UserInfo,
  NotificationSettings,
  PhoneVerification,
  SlackInfo,
  TelegramInfo,
  MobileAppVerification,
  MatrixInfo,
}

export interface UserFormData extends Partial<User> {
  slack_user_identity_name?: string;
  telegram_configuration_telegram_nick_name?: string;
  role?: UserRole;
}
