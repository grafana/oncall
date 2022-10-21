import { User } from 'models/user/user.types';

export const getIfChatOpsConnected = (user: User) => user?.slack_user_identity || user?.telegram_configuration;
