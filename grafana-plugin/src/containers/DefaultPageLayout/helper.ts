import { ApiSchemas } from 'network/oncall-api/api.types';

export const getIfChatOpsConnected = (user: ApiSchemas['User']) => {
  return user?.slack_user_identity || user?.telegram_configuration || user?.messaging_backends?.MSTEAMS;
};
