import { SelectOptions } from '@grafana/ui';
import dayjs from 'dayjs';
import { omit, reject } from 'lodash-es';
import { action, observable, toJS } from 'mobx';
import ReactCSSTransitionGroup from 'react-transition-group'; // ES6

import BaseStore from 'models/base_store';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { makeRequest } from 'network';
import { RootStore } from 'state';
import { SelectOption } from 'state/types';

import {
  enrichLayers,
  enrichOverrides,
  fillGaps,
  getFromString,
  splitToLayers,
  splitToShiftsAndFillGaps,
} from './schedule.helpers';
import { Events, Rotation, RotationType, Schedule, ScheduleEvent, Shift, Event, Layer } from './schedule.types';

const DEFAULT_FORMAT = 'YYYY-MM-DDTHH:mm:ss';

let I = 0;

export class ScheduleStore extends BaseStore {
  @observable
  searchResult: { [key: string]: Array<Schedule['id']> } = {};

  @observable.shallow
  items: { [id: string]: Schedule } = {};

  @observable.shallow
  shifts: { [id: string]: Shift } = {};

  @observable.shallow
  relatedEscalationChains: { [id: string]: EscalationChain[] } = {};

  @observable.shallow
  relatedUsers: { [id: string]: { [key: string]: Event } } = {};

  @observable.shallow
  rotations: {
    [id: string]: {
      [startMoment: string]: Rotation;
    };
  } = {};

  @observable.shallow
  events: {
    [scheduleId: string]: {
      [type: string]: {
        [startMoment: string]: Array<{ shiftId: string; events: Event[]; isPreview?: boolean }> | Layer[];
      };
    };
  } = {};

  @observable
  finalPreview?: Array<{ shiftId: Shift['id']; events: Event[] }>;

  @observable
  rotationPreview?: Layer[];

  @observable
  overridePreview?: Array<{ shiftId: Shift['id']; isPreview?: boolean; events: Event[] }>;

  @observable
  scheduleToScheduleEvents: {
    [id: string]: ScheduleEvent[];
  } = {};

  @observable
  byDayOptions: SelectOption[];

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/schedules/';
  }

  @action
  async loadItem(id: Schedule['id'], skipErrorHandling = false): Promise<Schedule> {
    const schedule = await this.getById(id, skipErrorHandling);

    this.items = {
      ...this.items,
      [id]: schedule,
    };

    return schedule;
  }

  @action
  async updateScheduleEvents(
    scheduleId: Schedule['id'],
    withEmpty: boolean,
    with_gap: boolean,
    date: string,
    user_tz: string
  ) {
    const { events } = await makeRequest(`/schedules/${scheduleId}/events/`, {
      params: { date, user_tz, with_empty: withEmpty, with_gap: with_gap },
    });

    this.scheduleToScheduleEvents = {
      ...this.scheduleToScheduleEvents,
      [scheduleId]: events,
    };
  }

  @action
  async updateItems(query = '') {
    const result = await makeRequest(this.path, { method: 'GET', params: { search: query } });

    this.items = {
      ...this.items,
      ...result.reduce(
        (acc: { [key: number]: Schedule }, item: Schedule) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };

    this.searchResult = {
      ...this.searchResult,
      [query]: result.map((item: Schedule) => item.id),
    };
  }

  async updateItem(id: Schedule['id'], fromOrganization = false) {
    if (id) {
      const item = await this.getById(id, true, fromOrganization);

      this.items = {
        ...this.items,
        [item.id]: item,
      };
    }
  }

  getSearchResult(query = '') {
    if (!this.searchResult[query]) {
      return undefined;
    }

    return this.searchResult[query].map((scheduleId: Schedule['id']) => this.items[scheduleId]);
  }

  @action
  async reloadIcal(scheduleId: Schedule['id']) {
    await makeRequest(`/schedules/${scheduleId}/reload_ical/`, {
      method: 'POST',
    });
  }

  async getICalLink(scheduleId: Schedule['id']) {
    return await makeRequest(`/schedules/${scheduleId}/export_token/`, {
      method: 'GET',
    });
  }

  async createICalLink(scheduleId: Schedule['id']) {
    return await makeRequest(`/schedules/${scheduleId}/export_token/`, {
      method: 'POST',
    });
  }

  async deleteICalLink(scheduleId: Schedule['id']) {
    await makeRequest(`/schedules/${scheduleId}/export_token/`, {
      method: 'DELETE',
    });
  }

  // ------- NEW SCHEDULES API ENDPOINTS ---------

  async createRotation(scheduleId: Schedule['id'], isOverride: boolean, params: Partial<Shift>) {
    const type = isOverride ? 3 : 2;

    const response = await makeRequest(`/oncall_shifts/`, {
      data: { type, schedule: scheduleId, ...params },
      method: 'POST',
    }).catch(this.onApiError);

    this.shifts = {
      ...this.shifts,
      [response.id]: response,
    };

    return response;
  }

  async updateRotationPreview(
    scheduleId: Schedule['id'],
    shiftId: Shift['id'] | 'new',
    fromString: string,
    isOverride: boolean,
    params: Partial<Shift>
  ) {
    const type = isOverride ? 3 : 2;

    const response = await makeRequest(`/oncall_shifts/preview/`, {
      params: { date: fromString },
      data: { type, schedule: scheduleId, shift_pk: shiftId === 'new' ? undefined : shiftId, ...params },
      method: 'POST',
    }).catch(this.onApiError);

    if (isOverride) {
      this.overridePreview = enrichOverrides(
        [...(this.events[scheduleId]?.['override']?.[fromString] as Array<{ shiftId: string; events: Event[] }>)],
        response.rotation,
        shiftId
      );
    } else {
      const layers = enrichLayers(
        [...(this.events[scheduleId]?.['rotation']?.[fromString] as Layer[])],
        response.rotation,
        shiftId,
        params.priority_level
      );

      this.rotationPreview = layers;
    }

    this.finalPreview = splitToShiftsAndFillGaps(response.final); /*.filter((shift) => shift.shiftId !== shiftId);*/
  }

  @action
  clearPreview() {
    this.finalPreview = undefined;
    this.rotationPreview = undefined;
    this.overridePreview = undefined;
  }

  async updateRotation(shiftId: Shift['id'], params: Partial<Shift>) {
    const response = await makeRequest(`/oncall_shifts/${shiftId}`, {
      data: { ...params },
      method: 'PUT',
    }).catch(this.onApiError);

    this.shifts = {
      ...this.shifts,
      [response.id]: response,
    };

    return response;
  }

  updateRelatedEscalationChains = async (id: Schedule['id']) => {
    const response = await makeRequest(`/schedules/${id}/related_escalation_chains`, {
      method: 'GET',
    });

    this.relatedEscalationChains = {
      ...this.relatedEscalationChains,
      [id]: response,
    };

    return response;
  };

  updateRelatedUsers = async (id: Schedule['id']) => {
    const { users } = await makeRequest(`/schedules/${id}/next_shifts_per_user`, {
      method: 'GET',
    });

    this.relatedUsers = {
      ...this.relatedUsers,
      [id]: users,
    };

    return users;
  };

  async updateOncallShifts(scheduleId: Schedule['id']) {
    const { results } = await makeRequest(`/oncall_shifts/`, {
      params: {
        schedule_id: scheduleId,
      },
      method: 'GET',
    });

    this.shifts = {
      ...this.shifts,
      ...results.reduce(
        (acc: { [key: number]: Shift }, item: Shift) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };
  }

  @action
  async updateOncallShift(shiftId: Shift['id']) {
    const response = await makeRequest(`/oncall_shifts/${shiftId}`, {});

    this.shifts = {
      ...this.shifts,
      [shiftId]: response,
    };

    return response;
  }

  async deleteOncallShift(shiftId: Shift['id']) {
    return await makeRequest(`/oncall_shifts/${shiftId}`, {
      method: 'DELETE',
    }).catch(this.onApiError);
  }

  async updateEvents(scheduleId: Schedule['id'], startMoment: dayjs.Dayjs, type: RotationType = 'rotation', days = 9) {
    const dayBefore = startMoment.subtract(1, 'day');

    const response = await makeRequest(`/schedules/${scheduleId}/filter_events/`, {
      params: {
        type,
        date: getFromString(dayBefore),
        days,
      },
      method: 'GET',
    });

    const fromString = getFromString(startMoment);

    const shifts = splitToShiftsAndFillGaps(response.events);

    // merge users on frontend side, we don't need it now
    /*shifts.forEach((shift) => {
      for (let i = 0; i < shift.events.length; i++) {
        const iEvent = shift.events[i];

        for (let j = i + 1; j < shift.events.length; j++) {
          const jEvent = shift.events[j];
          if (iEvent.start === jEvent.start && iEvent.end === jEvent.end) {
            iEvent.users.push(...jEvent.users);
            jEvent.merged = true;
          }
        }
        shift.events = shift.events.filter((event) => !event.merged);
      }
    });*/

    const layers = type === 'rotation' ? splitToLayers(shifts) : undefined;

    this.events = {
      ...this.events,
      [scheduleId]: {
        ...this.events[scheduleId],
        [type]: {
          ...this.events[scheduleId]?.[type],
          [fromString]: layers ? layers : shifts,
        },
      },
    };

    // console.log(toJS(this.events));
  }

  async updateFrequencyOptions() {
    return await makeRequest(`/oncall_shifts/frequency_options/`, {
      method: 'GET',
    });
  }

  async updateDaysOptions() {
    this.byDayOptions = await makeRequest(`/oncall_shifts/days_options/`, {
      method: 'GET',
    });
  }
}
