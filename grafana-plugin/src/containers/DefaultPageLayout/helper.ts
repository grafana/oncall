/**
 * TODO: update to absolute import
 * https://github.com/grafana/oncall-private/issues/1517
 */
import { User } from 'models/user/user.types';

export const getIfChatOpsConnected = (user: User) => {
  return user?.slack_user_identity || user?.telegram_configuration || user?.messaging_backends?.MSTEAMS;
};
