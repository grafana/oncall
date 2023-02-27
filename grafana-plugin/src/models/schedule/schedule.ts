import dayjs from 'dayjs';
import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { makeRequest } from 'network';
import { RootStore } from 'state';
import { SelectOption } from 'state/types';

import {
  enrichLayers,
  enrichOverrides,
  getFromString,
  splitToLayers,
  splitToShiftsAndFillGaps,
} from './schedule.helpers';
import {
  Rotation,
  RotationType,
  Schedule,
  ScheduleEvent,
  Shift,
  Event,
  Layer,
  ShiftEvents,
  RotationFormLiveParams,
} from './schedule.types';

export class ScheduleStore extends BaseStore {
  @observable
  searchResult: { count?: number; results?: Array<Schedule['id']> } = {};

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
        [startMoment: string]: ShiftEvents[] | Layer[];
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
  rotationFormLiveParams: RotationFormLiveParams = undefined;

  @observable
  scheduleToScheduleEvents: {
    [id: string]: ScheduleEvent[];
  } = {};

  @observable
  byDayOptions: SelectOption[];

  @observable
  scheduleId: Schedule['id'];

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
  async updateItems(f: any = { searchTerm: '', type: undefined }, page = 1) {
    const filters = typeof f === 'string' ? { searchTerm: f } : f;
    const { searchTerm: search, type } = filters;
    const { count, results } = await makeRequest(this.path, { method: 'GET', params: { search: search, type, page } });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc: { [key: number]: Schedule }, item: Schedule) => ({
          ...acc,
          [item.id]: item,
        }),
        {}
      ),
    };
    this.searchResult = {
      count,
      results: results.map((item: Schedule) => item.id),
    };
  }

  async updateItem(id: Schedule['id'], fromOrganization = false) {
    if (id) {
      const item = await this.getById(id, true, fromOrganization);

      this.items = {
        ...this.items,
        [item.id]: item,
      };

      return item;
    }
  }

  getSearchResult() {
    if (!this.searchResult) {
      return undefined;
    }
    return {
      count: this.searchResult.count,
      results: this.searchResult.results?.map((scheduleId: Schedule['id']) => this.items[scheduleId]),
    };
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

  setRotationFormLiveParams(params: RotationFormLiveParams) {
    this.rotationFormLiveParams = params;
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

    this.finalPreview = splitToShiftsAndFillGaps(response.final);
  }

  @action
  clearPreview() {
    this.finalPreview = undefined;
    this.rotationPreview = undefined;
    this.overridePreview = undefined;
    this.rotationFormLiveParams = undefined;
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
