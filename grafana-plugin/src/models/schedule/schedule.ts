import dayjs from 'dayjs';
import { action, observable } from 'mobx';

import { RemoteFiltersType } from 'containers/RemoteFilters/RemoteFilters.types';
import BaseStore from 'models/base_store';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { User } from 'models/user/user.types';
import { makeRequest } from 'network';
import { RootStore } from 'state';
import { SelectOption } from 'state/types';

import {
  createShiftSwapEventFromShiftSwap,
  enrichLayers,
  enrichOverrides,
  flattenShiftEvents,
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
  ScheduleScoreQualityResponse,
  ShiftSwap,
} from './schedule.types';

export class ScheduleStore extends BaseStore {
  @observable
  searchResult: { count?: number; results?: Array<Schedule['id']> } = {};

  @observable.shallow
  items: { [id: string]: Schedule } = {};

  @observable.shallow
  shifts: { [id: string]: Shift } = {};

  shiftsCurrentlyUpdating = {};

  @observable.shallow
  relatedEscalationChains: { [id: string]: EscalationChain[] } = {};

  @observable.shallow
  relatedUsers: { [id: string]: { [key: string]: Event } } = {};

  @observable.shallow
  shiftSwaps: { [id: string]: ShiftSwap } = {};

  @observable.shallow
  scheduleAndDateToShiftSwaps: { [scheduleId: string]: { [date: string]: ShiftEvents[] } } = {};

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

  @observable.shallow
  personalEvents: {
    [userPk: string]: {
      [startMoment: string]: ShiftEvents[];
    };
  } = {};

  @observable.shallow
  onCallNow: {
    [userPk: string]: boolean;
  } = {};

  @observable
  finalPreview?: { [fromString: string]: Array<{ shiftId: Shift['id']; events: Event[] }> };

  @observable
  rotationPreview?: { [fromString: string]: Layer[] };

  @observable
  shiftSwapsPreview?: {
    [fromString: string]: ShiftEvents[];
  };

  @observable
  overridePreview?: { [fromString: string]: ShiftEvents[] };

  @observable
  rotationFormLiveParams: RotationFormLiveParams = undefined;

  @observable
  scheduleToScheduleEvents: {
    [id: string]: ScheduleEvent[];
  } = {};

  @observable
  byDayOptions: SelectOption[] = [];

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
  async updateItems(
    f: RemoteFiltersType | string = { searchTerm: '', type: undefined, used: undefined },
    page = 1,
    shouldUpdateFn: () => boolean = undefined
  ) {
    const filters = typeof f === 'string' ? { search: f } : f;
    const { count, results } = await makeRequest(this.path, {
      method: 'GET',
      params: { ...filters, page },
    });

    if (shouldUpdateFn && !shouldUpdateFn()) {
      return;
    }

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
      let schedule;
      try {
        schedule = await this.getById(id, true, fromOrganization);
      } catch (error) {
        if (error.response.data.error_code === 'wrong_team') {
          schedule = {
            id,
            name: '🔒 Private schedule',
            private: true,
          };
        }
      }

      if (schedule) {
        this.items = {
          ...this.items,
          [id]: schedule,
        };
      }

      return schedule;
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

  async getScoreQuality(scheduleId: Schedule['id']): Promise<ScheduleScoreQualityResponse> {
    return await makeRequest(`/schedules/${scheduleId}/quality`, { method: 'GET' });
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
    });

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
    startMoment: dayjs.Dayjs,
    isOverride: boolean,
    params: Partial<Shift>
  ) {
    const type = isOverride ? 3 : 2;

    const fromString = getFromString(startMoment);

    const dayBefore = startMoment.subtract(1, 'day');

    const response = await makeRequest(`/oncall_shifts/preview/`, {
      params: { date: getFromString(dayBefore), days: 8 },
      data: { type, schedule: scheduleId, shift_pk: shiftId === 'new' ? undefined : shiftId, ...params },
      method: 'POST',
    });

    if (isOverride) {
      const overridePreview = enrichOverrides(
        [...(this.events[scheduleId]?.['override']?.[fromString] as Array<{ shiftId: string; events: Event[] }>)],
        response.rotation,
        shiftId
      );

      this.overridePreview = { ...this.overridePreview, [fromString]: overridePreview };
    } else {
      const layers = enrichLayers(
        [...(this.events[scheduleId]?.['rotation']?.[fromString] as Layer[])],
        response.rotation,
        shiftId,
        params.priority_level
      );

      this.rotationPreview = { ...this.rotationPreview, [fromString]: layers };
    }

    this.finalPreview = { ...this.finalPreview, [fromString]: splitToShiftsAndFillGaps(response.final) };
  }

  @action
  async updateShiftsSwapPreview(scheduleId: Schedule['id'], startMoment: dayjs.Dayjs, params: Partial<ShiftSwap>) {
    const fromString = getFromString(startMoment);

    const newShiftEvents: ShiftEvents = {
      shiftId: 'new',
      events: [createShiftSwapEventFromShiftSwap(params)],
      isPreview: true,
    };

    if (!this.scheduleAndDateToShiftSwaps[scheduleId][fromString]) {
      await this.updateShiftSwaps(scheduleId, startMoment);
    }

    const existingShiftEventsList: ShiftEvents[] = this.scheduleAndDateToShiftSwaps[scheduleId][fromString];

    const shiftEventsListFlattened = flattenShiftEvents([...existingShiftEventsList, newShiftEvents]);

    this.shiftSwapsPreview = {
      ...this.shiftSwapsPreview,
      [fromString]: shiftEventsListFlattened,
    };
  }

  @action
  clearPreview() {
    this.finalPreview = undefined;
    this.rotationPreview = undefined;
    this.overridePreview = undefined;
    this.shiftSwapsPreview = undefined;
    this.rotationFormLiveParams = undefined;
  }

  async updateRotation(shiftId: Shift['id'], params: Partial<Shift>) {
    const response = await makeRequest(`/oncall_shifts/${shiftId}`, {
      params: { force: true },
      data: { ...params },
      method: 'PUT',
    });

    this.shifts = {
      ...this.shifts,
      [response.id]: response,
    };

    return response;
  }

  async updateRotationAsNew(shiftId: Shift['id'], params: Partial<Shift>) {
    const response = await makeRequest(`/oncall_shifts/${shiftId}`, {
      data: { ...params },
      method: 'PUT',
    });

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
    if (this.shiftsCurrentlyUpdating[shiftId]) {
      return;
    }

    this.shiftsCurrentlyUpdating[shiftId] = true;

    const response = await makeRequest(`/oncall_shifts/${shiftId}`, {});

    this.shifts = {
      ...this.shifts,
      [shiftId]: response,
    };

    delete this.shiftsCurrentlyUpdating[shiftId];

    return response;
  }

  @action
  async saveOncallShift(shiftId: Shift['id'], data: Partial<Shift>) {
    const response = await makeRequest(`/oncall_shifts/${shiftId}`, { method: 'PUT', data });

    this.shifts = {
      ...this.shifts,
      [shiftId]: response,
    };

    return response;
  }

  async deleteOncallShift(shiftId: Shift['id'], force?: boolean) {
    return await makeRequest(`/oncall_shifts/${shiftId}`, {
      method: 'DELETE',
      params: { force },
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

  async createShiftSwap(params: Partial<ShiftSwap>) {
    return await makeRequest(`/shift_swaps/`, { method: 'POST', data: params }).catch(this.onApiError);
  }

  async deleteShiftSwap(shiftSwapId: ShiftSwap['id']) {
    return await makeRequest(`/shift_swaps/${shiftSwapId}`, { method: 'DELETE' }).catch(this.onApiError);
  }

  async takeShiftSwap(shiftSwapId: ShiftSwap['id']) {
    return await makeRequest(`/shift_swaps/${shiftSwapId}/take`, { method: 'POST' }).catch(this.onApiError);
  }

  async loadShiftSwap(id: ShiftSwap['id']) {
    const result = await makeRequest(`/shift_swaps/${id}`, { params: { expand_users: true } });

    this.shiftSwaps = { ...this.shiftSwaps, [id]: result };

    return result;
  }

  async updateShiftSwaps(scheduleId: Schedule['id'], startMoment: dayjs.Dayjs, days = 9) {
    const fromString = getFromString(startMoment);

    const dayBefore = startMoment.subtract(1, 'day');

    const result = await makeRequest(`/schedules/${scheduleId}/filter_shift_swaps/`, {
      method: 'GET',
      params: {
        date: getFromString(dayBefore),
        days,
      },
    });

    const shiftEventsList: ShiftEvents[] = result.shift_swaps.map((shiftSwap) => ({
      shiftId: shiftSwap.id,
      events: [createShiftSwapEventFromShiftSwap(shiftSwap)],
      isPreview: false,
    }));

    const shiftEventsListFlattened = flattenShiftEvents(shiftEventsList);

    this.shiftSwaps = result.shift_swaps.reduce(
      (memo, shiftSwap) => ({
        ...memo,
        [shiftSwap.id]: shiftSwap,
      }),
      this.shiftSwaps
    );

    this.scheduleAndDateToShiftSwaps = {
      ...this.scheduleAndDateToShiftSwaps,
      [scheduleId]: {
        ...this.scheduleAndDateToShiftSwaps[scheduleId],
        [fromString]: shiftEventsListFlattened,
      },
    };
  }

  async updatePersonalEvents(userPk: User['pk'], startMoment: dayjs.Dayjs, days = 9) {
    const fromString = getFromString(startMoment);

    const dayBefore = startMoment.subtract(1, 'day');

    const { is_oncall, schedules } = await makeRequest(`/schedules/current_user_events/`, {
      method: 'GET',
      params: {
        date: getFromString(dayBefore),
        days,
      },
    });

    const shiftEventsList = schedules.reduce((acc, schedule) => {
      return [...acc, ...splitToShiftsAndFillGaps(schedule.events)];
    }, []);

    const shiftEventsListFlattened = flattenShiftEvents(shiftEventsList);

    this.personalEvents = {
      ...this.personalEvents,
      [userPk]: {
        ...this.personalEvents[userPk],
        [fromString]: shiftEventsListFlattened,
      },
    };

    this.onCallNow = {
      ...this.onCallNow,
      [userPk]: is_oncall,
    };
  }
}
