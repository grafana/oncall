import dayjs from 'dayjs';
import { action, makeObservable, observable, runInAction } from 'mobx';

import { PageErrorData } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import { getWrongTeamResponseInfo } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import { RemoteFiltersType } from 'containers/RemoteFilters/RemoteFilters.types';
import { BaseStore } from 'models/base_store';
import { EscalationChain } from 'models/escalation_chain/escalation_chain.types';
import { ActionKey } from 'models/loader/action-keys';
import { makeRequest } from 'network/network';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { RootStore } from 'state/rootStore';
import { SelectOption } from 'state/types';
import { AutoLoadingState } from 'utils/decorators';

import {
  createShiftSwapEventFromShiftSwap,
  enrichEventsWithScheduleData,
  enrichLayers,
  enrichOverrides,
  fillGapsInShifts,
  flattenShiftEvents,
  getFromString,
  getTotalDaysToDisplay,
  splitToLayers,
  splitToShifts,
  unFlattenShiftEvents,
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
  ScheduleScoreQualityResponse,
  ShiftSwap,
  ScheduleView,
} from './schedule.types';

export class ScheduleStore extends BaseStore {
  @observable
  searchResult: { page_size?: number; count?: number; results?: Array<Schedule['id']> } = {};

  @observable.shallow
  items: { [id: string]: Schedule } = {};

  @observable
  quality: ScheduleScoreQualityResponse;

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
  scheduleToScheduleEvents: {
    [id: string]: ScheduleEvent[];
  } = {};

  @observable
  byDayOptions: SelectOption[] = [];

  @observable
  refreshEventsError?: Partial<PageErrorData> = {
    isWrongTeamError: false,
    wrongTeamNoPermissions: false,
  };

  @observable
  scheduleView = ScheduleView.OneWeek;

  constructor(rootStore: RootStore) {
    super(rootStore);

    makeObservable(this);

    this.path = '/schedules/';
  }

  @action.bound
  setScheduleView(value: ScheduleView) {
    this.scheduleView = value;
  }

  @action.bound
  async loadItem(id: Schedule['id'], skipErrorHandling = false): Promise<Schedule> {
    const schedule = await this.getById(id, skipErrorHandling);

    runInAction(() => {
      this.items = {
        ...this.items,
        [id]: schedule,
      };
    });

    return schedule;
  }

  @action.bound
  async updateItems(
    f: RemoteFiltersType | string = { searchTerm: '', type: undefined, used: undefined },
    page = 1,
    invalidateFn: () => boolean = undefined
  ) {
    const filters = typeof f === 'string' ? { search: f } : f;
    const { page_size, count, results } = await makeRequest(this.path, {
      method: 'GET',
      params: { ...filters, page },
    });

    if (invalidateFn && invalidateFn()) {
      return;
    }

    runInAction(() => {
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
        page_size,
        count,
        results: results.map((item: Schedule) => item.id),
      };
    });
  }

  @action.bound
  async updateItem(id: Schedule['id'], fromOrganization = false) {
    if (id) {
      let schedule;
      try {
        schedule = await this.getById(id, true, fromOrganization);
      } catch (error) {
        if (error.response.data?.error_code === 'wrong_team') {
          schedule = {
            id,
            name: '🔒 Private schedule',
            private: true,
          };
        }
      }

      if (schedule) {
        runInAction(() => {
          this.items = {
            ...this.items,
            [id]: schedule,
          };
        });
      }

      return schedule;
    }
  }

  getSearchResult = () => {
    return {
      page_size: this.searchResult.page_size,
      count: this.searchResult.count,
      results: this.searchResult.results?.map((scheduleId: Schedule['id']) => this.items[scheduleId]),
    };
  };

  @action.bound
  async getScoreQuality(scheduleId: Schedule['id']) {
    const [quality] = await Promise.all([
      makeRequest(`/schedules/${scheduleId}/quality`, { method: 'GET' }),
      this.updateRelatedEscalationChains(scheduleId),
    ]);
    runInAction(() => {
      this.quality = quality;
    });
  }

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

  @action.bound
  async createRotation(scheduleId: Schedule['id'], isOverride: boolean, params: Partial<Shift>) {
    const type = isOverride ? 3 : 2;

    const response = await makeRequest(`/oncall_shifts/`, {
      data: { type, schedule: scheduleId, ...params },
      method: 'POST',
    });
    await this.rootStore.scheduleStore.refreshEvents(scheduleId);
    await this.getScoreQuality(scheduleId);

    runInAction(() => {
      this.shifts = {
        ...this.shifts,
        [response.id]: response,
      };
    });

    return response;
  }

  async updateRotationPreview(
    scheduleId: Schedule['id'],
    shiftId: Shift['id'] | 'new',
    startMoment: dayjs.Dayjs,
    isOverride: boolean,
    params: Partial<Shift>
  ) {
    const type = isOverride ? 3 : 2;

    const days = getTotalDaysToDisplay(this.scheduleView, this.rootStore.timezoneStore.calendarStartDate);

    const fromString = getFromString(startMoment);

    const dayBefore = startMoment.subtract(1, 'day');

    const response = await makeRequest(`/oncall_shifts/preview/`, {
      params: { date: getFromString(dayBefore), days },
      data: { type, schedule: scheduleId, shift_pk: shiftId === 'new' ? undefined : shiftId, ...params },
      method: 'POST',
    });

    runInAction(() => {
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

      this.finalPreview = { ...this.finalPreview, [fromString]: fillGapsInShifts(splitToShifts(response.final)) };
    });
  }

  @action.bound
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

    runInAction(() => {
      this.shiftSwapsPreview = {
        ...this.shiftSwapsPreview,
        [fromString]: shiftEventsListFlattened,
      };
    });
  }

  @action.bound
  clearPreview() {
    this.finalPreview = undefined;
    this.rotationPreview = undefined;
    this.overridePreview = undefined;
    this.shiftSwapsPreview = undefined;
  }

  @action.bound
  async updateRotation(shiftId: Shift['id'], params: Partial<Shift>) {
    const response = await makeRequest(`/oncall_shifts/${shiftId}`, {
      params: { force: true },
      data: { ...params },
      method: 'PUT',
    });

    runInAction(() => {
      this.shifts = {
        ...this.shifts,
        [response.id]: response,
      };
    });

    return response;
  }

  @action.bound
  async updateRotationAsNew(shiftId: Shift['id'], params: Partial<Shift>) {
    const response = await makeRequest(`/oncall_shifts/${shiftId}`, {
      data: { ...params },
      method: 'PUT',
    });

    runInAction(() => {
      this.shifts = {
        ...this.shifts,
        [response.id]: response,
      };
    });

    return response;
  }

  @action.bound
  updateRelatedEscalationChains = async (id: Schedule['id']) => {
    const response = await makeRequest(`/schedules/${id}/related_escalation_chains`, {
      method: 'GET',
    });

    runInAction(() => {
      this.relatedEscalationChains = {
        ...this.relatedEscalationChains,
        [id]: response,
      };
    });

    return response;
  };

  @action.bound
  updateRelatedUsers = async (id: Schedule['id']) => {
    const { users } = await makeRequest(`/schedules/${id}/next_shifts_per_user`, {
      method: 'GET',
    });

    runInAction(() => {
      this.relatedUsers = {
        ...this.relatedUsers,
        [id]: users,
      };
    });

    return users;
  };

  @action.bound
  async updateOncallShifts(scheduleId: Schedule['id']) {
    const { results } = await makeRequest(`/oncall_shifts/`, {
      params: {
        schedule_id: scheduleId,
      },
      method: 'GET',
    });

    runInAction(() => {
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
    });
  }

  @action.bound
  async updateOncallShift(shiftId: Shift['id']) {
    if (this.shiftsCurrentlyUpdating[shiftId]) {
      return;
    }

    this.shiftsCurrentlyUpdating[shiftId] = true;

    const response = await makeRequest(`/oncall_shifts/${shiftId}`, {});

    runInAction(() => {
      this.shifts = {
        ...this.shifts,
        [shiftId]: response,
      };
    });

    delete this.shiftsCurrentlyUpdating[shiftId];

    return response;
  }

  @action.bound
  async saveOncallShift(shiftId: Shift['id'], data: Partial<Shift>) {
    const response = await makeRequest(`/oncall_shifts/${shiftId}`, { method: 'PUT', data });

    runInAction(() => {
      this.shifts = {
        ...this.shifts,
        [shiftId]: response,
      };
    });

    return response;
  }

  async deleteOncallShift(shiftId: Shift['id'], force?: boolean) {
    try {
      return await makeRequest(`/oncall_shifts/${shiftId}`, {
        method: 'DELETE',
        params: { force },
      });
    } catch (err) {
      this.onApiError(err);
    }
  }

  @action.bound
  async updateEvents(scheduleId: Schedule['id'], startMoment: dayjs.Dayjs, type: RotationType = 'rotation', days) {
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
    const shiftsRaw = splitToShifts(response.events);
    const shiftsUnflattened = unFlattenShiftEvents(shiftsRaw);
    const shifts = fillGapsInShifts(shiftsUnflattened);
    const layers = type === 'rotation' ? splitToLayers(shifts) : undefined;

    runInAction(() => {
      this.events = {
        ...this.events,
        [scheduleId]: {
          ...this.events[scheduleId],
          [type]: {
            ...this.events[scheduleId]?.[type],
            [fromString]: layers || shifts,
          },
        },
      };
    });
  }

  @action.bound
  async refreshEvents(scheduleId: string, scheduleView?: ScheduleView) {
    this.refreshEventsError = {};
    const startMoment = this.rootStore.timezoneStore.calendarStartDate;

    const days =
      getTotalDaysToDisplay(scheduleView || this.scheduleView, this.rootStore.timezoneStore.calendarStartDate) + 2;

    try {
      const schedule = await this.loadItem(scheduleId);
      this.rootStore.setPageTitle(schedule?.name);
    } catch (error) {
      runInAction(() => {
        this.refreshEventsError = getWrongTeamResponseInfo(error);
      });
    }

    this.updateRelatedUsers(scheduleId); // to refresh related users
    await Promise.all([
      this.updateEvents(scheduleId, startMoment, 'rotation', days),
      this.updateEvents(scheduleId, startMoment, 'override', days),
      this.updateEvents(scheduleId, startMoment, 'final', days),
      this.updateShiftSwaps(scheduleId, startMoment),
    ]);
  }

  async updateFrequencyOptions() {
    return await makeRequest(`/oncall_shifts/frequency_options/`, {
      method: 'GET',
    });
  }

  @action.bound
  async updateDaysOptions() {
    const result = await makeRequest(`/oncall_shifts/days_options/`, {
      method: 'GET',
    });

    runInAction(() => {
      this.byDayOptions = result;
    });
  }

  async createShiftSwap(params: Partial<ShiftSwap>) {
    try {
      return await makeRequest(`/shift_swaps/`, { method: 'POST', data: params });
    } catch (err) {
      this.onApiError(err);
    }
  }

  async deleteShiftSwap(shiftSwapId: ShiftSwap['id']) {
    try {
      return await makeRequest(`/shift_swaps/${shiftSwapId}`, { method: 'DELETE' });
    } catch (err) {
      this.onApiError(err);
    }
  }

  async takeShiftSwap(shiftSwapId: ShiftSwap['id']) {
    try {
      return await makeRequest(`/shift_swaps/${shiftSwapId}/take`, { method: 'POST' });
    } catch (err) {
      this.onApiError(err);
    }
  }

  @action.bound
  async loadShiftSwap(id: ShiftSwap['id']) {
    const result = await makeRequest(`/shift_swaps/${id}`, { params: { expand_users: true } });

    runInAction(() => {
      this.shiftSwaps = { ...this.shiftSwaps, [id]: result };
    });

    return result;
  }

  @action.bound
  async updateShiftSwaps(scheduleId: Schedule['id'], startMoment: dayjs.Dayjs) {
    const fromString = getFromString(startMoment);

    const days = getTotalDaysToDisplay(this.scheduleView, this.rootStore.timezoneStore.calendarStartDate) + 2;

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

    runInAction(() => {
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
    });
  }

  @AutoLoadingState(ActionKey.UPDATE_PERSONAL_EVENTS)
  @action.bound
  async updatePersonalEvents(userPk: ApiSchemas['User']['pk'], startMoment: dayjs.Dayjs, isUpdateOnCallNow = false) {
    const fromString = getFromString(startMoment);

    const days = getTotalDaysToDisplay(ScheduleView.OneWeek, this.rootStore.timezoneStore.calendarStartDate) + 2;

    const dayBefore = startMoment.subtract(1, 'day');

    const { is_oncall, schedules } = await makeRequest(`/schedules/current_user_events/`, {
      method: 'GET',
      params: {
        date: getFromString(dayBefore),
        days,
      },
    });

    const shiftEventsList = schedules.reduce((acc, { events, id, name }) => {
      return [...acc, ...fillGapsInShifts(splitToShifts(enrichEventsWithScheduleData(events, { id, name })))];
    }, []);

    const shiftEventsListFlattened = flattenShiftEvents(shiftEventsList);

    runInAction(() => {
      this.personalEvents = {
        ...this.personalEvents,
        [userPk]: {
          ...this.personalEvents[userPk],
          [fromString]: shiftEventsListFlattened,
        },
      };

      if (isUpdateOnCallNow) {
        // since current endpoint works incorrectly we are waiting for https://github.com/grafana/oncall/issues/3164
        this.onCallNow = {
          ...this.onCallNow,
          [userPk]: is_oncall,
        };
      }
    });
  }
}
