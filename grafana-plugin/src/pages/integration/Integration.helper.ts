import { IconName } from '@grafana/ui';
import dayjs from 'dayjs';

import { MaintenanceMode } from 'models/alert_receive_channel/alert_receive_channel.types';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { AppFeature } from 'state/features';
import { RootStore } from 'state/rootStore';

import { MAX_CHARACTERS_COUNT, TEXTAREA_ROWS_COUNT } from './IntegrationCommon.config';

export const IntegrationHelper = {
  isSpecificIntegration: (alertReceiveChannel: ApiSchemas['AlertReceiveChannel'] | string, name: string) => {
    if (!alertReceiveChannel) {
      return false;
    }

    if (typeof alertReceiveChannel === 'string') {
      return name === alertReceiveChannel;
    }

    return name === alertReceiveChannel.integration;
  },

  getFilteredTemplate: (template: string, isTextArea: boolean): string => {
    if (!template) {
      return '';
    }

    const lines = template.split('\n');
    if (isTextArea) {
      return lines
        .slice(0, TEXTAREA_ROWS_COUNT + 1)
        .map((line) => IntegrationHelper.truncateLine(line))
        .join('\n');
    }

    return IntegrationHelper.truncateLine(lines[0]);
  },

  truncateLine: (line: string, maxCharacterCount: number = MAX_CHARACTERS_COUNT): string => {
    if (!line || !line.trim()) {
      return '';
    }

    const slice = line.substring(0, maxCharacterCount);
    return slice.length === line.length ? slice : `${slice} ...`;
  },

  getMaintenanceText(maintenanceUntill: number, mode?: MaintenanceMode) {
    const date = dayjs(new Date(maintenanceUntill * 1000));
    const now = dayjs();
    const hourDiff = date.diff(now, 'hours');
    const minDiff = date.diff(now, 'minutes');
    const totalMinDiff = minDiff - hourDiff * 60;
    const totalDiffString = hourDiff > 0 ? `${hourDiff}h ${totalMinDiff}m left` : `${totalMinDiff}m left`;

    if (mode !== undefined) {
      return `${mode === MaintenanceMode.Debug ? 'Debug Maintenance' : 'Maintenance'}: ${totalDiffString}`;
    }

    return totalDiffString;
  },

  hasChatopsInstalled(store: RootStore) {
    const hasSlack = Boolean(store.organizationStore.currentOrganization?.slack_team_identity);
    const hasTelegram =
      store.hasFeature(AppFeature.Telegram) && store.telegramChannelStore.currentTeamToTelegramChannel?.length > 0;
    const isMSTeamsInstalled = Boolean(store.msteamsChannelStore.currentTeamToMSTeamsChannel?.length > 0);

    return hasSlack || hasTelegram || isMSTeamsInstalled;
  },

  getChatOpsChannels(channelFilter: ChannelFilter, store: RootStore): Array<{ name: string; icon: IconName }> {
    const channels: Array<{ name: string; icon: IconName }> = [];
    const telegram = Object.keys(store.telegramChannelStore.items).map((k) => store.telegramChannelStore.items[k]);

    if (store.hasFeature(AppFeature.Slack) && channelFilter.notify_in_slack) {
      const { currentOrganization } = store.organizationStore;

      const matchingSlackChannel = currentOrganization?.slack_channel?.id
        ? store.slackChannelStore.items[currentOrganization.slack_channel?.id]
        : undefined;
      if (channelFilter.slack_channel?.display_name || matchingSlackChannel?.display_name) {
        channels.push({
          name: channelFilter.slack_channel?.display_name || matchingSlackChannel?.display_name,
          icon: 'slack',
        });
      }
    }

    const matchingTelegram = telegram.find((t) => t.id === channelFilter.telegram_channel);

    if (
      store.hasFeature(AppFeature.Telegram) &&
      channelFilter.telegram_channel &&
      channelFilter.notify_in_telegram &&
      matchingTelegram?.channel_name
    ) {
      channels.push({
        name: matchingTelegram.channel_name,
        icon: 'telegram-alt',
      });
    }

    const { notification_backends } = channelFilter;
    const msteamsChannels = store.msteamsChannelStore.items;

    if (
      notification_backends?.MSTEAMS &&
      notification_backends?.MSTEAMS.enabled &&
      msteamsChannels[notification_backends.MSTEAMS.channel]
    ) {
      channels.push({
        name: msteamsChannels[notification_backends.MSTEAMS.channel].display_name,
        icon: 'microsoft',
      });
    }

    return channels;
  },
};

export const getIsBidirectionalIntegration = ({ integration }: ApiSchemas['AlertReceiveChannel']) =>
  integration === ('servicenow' as ApiSchemas['AlertReceiveChannel']['integration']); // TODO: add service now in backend schema as valid value and remove casting
