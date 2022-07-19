import dayjs from 'dayjs';
import { omit, reject } from 'lodash-es';
import { action, observable, toJS } from 'mobx';
import ReactCSSTransitionGroup from 'react-transition-group'; // ES6

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';

import { Rotation, Schedule, ScheduleEvent } from './schedule.types';

const DEFAULT_FORMAT = 'YYYY-MM-DDTHH:mm:ss';

function getUsers() {
  const rnd = Math.random();
  /*

        if (rnd > 0.66) {
          return [];
        }
*/

  const users = [
    'U5WE86241LNEA',
    'U9XM1G7KTE3KW',
    'UYKS64M6C59XM',
    'UFFIRDUFXA6W3',
    'UPRMSTP9LCADE',
    'UR6TVJWZYV19M',
    'UHRMQQ7KETPCS',
  ];

  /* if (rnd > 0.33) {
          return [users[Math.floor(Math.random() * users.length)], users[Math.floor(Math.random() * users.length)]];
        }*/

  return ['UPRMSTP9LCADE', 'UHRMQQ7KETPCS'];

  return [users[Math.floor(Math.random() * users.length)]];
}

export class ScheduleStore extends BaseStore {
  @observable
  searchResult: { [key: string]: Array<Schedule['id']> } = {};

  @observable.shallow
  items: { [id: string]: Schedule } = {};

  @observable.shallow
  rotations: { [id: string]: Rotation } = {};

  @observable
  scheduleToScheduleEvents: {
    [id: string]: ScheduleEvent[];
  } = {};

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/schedules/';
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
    const result = await this.getAll();

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

  async updateItem(id: Schedule['id']) {
    if (id) {
      const item = await this.getById(id);

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

  async createRotation(scheduleId: Schedule['id'], isOverride: boolean, params) {
    const type = isOverride ? 3 : 2;

    const { name, shift_start, shift_end, rotation_start } = params;

    return await makeRequest(`/oncall_shifts/`, {
      data: { name, type, schedule: scheduleId, shift_start, shift_end, rotation_start },
      method: 'POST',
    });
  }

  async updateRotation(rotationId: Rotation['id']) {
    return await makeRequest(`/oncall_shifts/`, {
      params: { shift_id: rotationId },
      method: 'GET',
    });
  }

  async updateRotationMock(rotationId: Rotation['id'], fromString: string) {
    const response = await new Promise((resolve, reject) => {
      setTimeout(() => {
        if (!fromString) {
          fromString = dayjs().startOf('week').format('YYYY-MM-DDTHH:mm:ss.000Z');
        }

        const startMoment = dayjs(fromString).utc();

        const shifts = [];
        for (let i = 0; i < 7; i++) {
          shifts.push({
            // start: dayjs(startMoment).add(12 * i, 'hour'),
            // duration: (Math.floor(Math.random() * 6) + 10) * 60 * 60,
            start: dayjs(startMoment).add(24 * i, 'hour'),
            // duration: (Math.floor(Math.random() * 6) + 10) * 60 * 60,
            duration: 24 * 60 * 60,
            users: getUsers(),
          });
        }

        resolve({ id: rotationId, shifts });
      }, 500);
    });

    this.rotations = {
      ...this.rotations,
      [rotationId]: response as Rotation,
    };
  }

  async updateFrequencyOptions(scheduleId: Schedule['id']) {
    return await makeRequest(`/oncall_shifts/frequency_options/`, {
      method: 'GET',
    });
  }

  async updateDaysOptions(scheduleId: Schedule['id']) {
    return await makeRequest(`/oncall_shifts/days_options/`, {
      method: 'GET',
    });
  }
}
