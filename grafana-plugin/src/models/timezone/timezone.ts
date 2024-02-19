import dayjs, { Dayjs } from 'dayjs';
import { observable, action, computed, makeObservable } from 'mobx';

// TODO: move utils from Schedule.helpers to common place
import { getStartOfWeekBasedOnCurrentDate } from 'pages/schedule/Schedule.helpers';
import { RootStore } from 'state/rootStore';

import { getOffsetOfCurrentUser, getGMTTimezoneLabelBasedOnOffset } from './timezone.helpers';

export class TimezoneStore {
  constructor(rootStore: RootStore) {
    makeObservable(this);

    this.rootStore = rootStore;
  }

  rootStore: RootStore;

  @observable
  selectedTimezoneOffset = getOffsetOfCurrentUser();

  @observable
  calendarStartDate = getStartOfWeekBasedOnCurrentDate(this.currentDateInSelectedTimezone);

  @action.bound
  async setSelectedTimezoneOffset(offset: number) {
    this.selectedTimezoneOffset = offset;
    this.calendarStartDate = getStartOfWeekBasedOnCurrentDate(this.currentDateInSelectedTimezone);
  }

  @action.bound
  setCalendarStartDate(date: Dayjs) {
    this.calendarStartDate = date;
  }

  @action.bound
  setSelectedTimezoneOffsetBasedOnTz(timezone: string) {
    this.selectedTimezoneOffset = dayjs().tz(timezone).utcOffset();
  }

  @action.bound
  getDateInSelectedTimezone(date: Dayjs | string) {
    if (typeof date === 'string') {
      date = dayjs(date);
    }
    return dayjs(date.format()).utcOffset(this.selectedTimezoneOffset);
  }

  @computed
  get selectedTimezoneLabel() {
    return getGMTTimezoneLabelBasedOnOffset(this.selectedTimezoneOffset);
  }

  @computed
  get currentDateInSelectedTimezone() {
    return dayjs().utcOffset(this.selectedTimezoneOffset);
  }
}
