import { Schedule } from 'models/schedule/schedule.types';

export function prepareForEdit(item: Schedule) {
  return {
    name: item.name,
    ical_url_primary: item.ical_url_primary,
    ical_url_overrides: item.ical_url_overrides,
    enable_web_overrides: item.enable_web_overrides,
    slack_channel_id: item.slack_channel?.id,
    user_group: item.user_group?.id,
    send_empty_shifts_report: item.send_empty_shifts_report,
    team: item.team,
    notify_oncall_shift_freq: item.notify_oncall_shift_freq,
    notify_empty_oncall: item.notify_empty_oncall,
    mention_oncall_start: item.mention_oncall_start,
    mention_oncall_next: item.mention_oncall_next,
    type: item.type,
  };
}
