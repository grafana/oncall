import { AppEvents } from '@grafana/data';
import { AxiosError } from 'axios';
import { sentenceCase } from 'change-case';
// @ts-ignore
import appEvents from 'grafana/app/core/app_events';
import { isArray, concat, isPlainObject, flatMap, map, keys } from 'lodash-es';
import qs from 'query-string';

export const TZ_OFFSET = new Date().getTimezoneOffset();

export const getTzOffsetHours = (): number => TZ_OFFSET / 60;

export const showApiError = (error: any) => {
  if (error.response.status >= 400 && error.response.status < 500) {
    const payload = error.response.data;
    const text =
      typeof payload === 'string'
        ? payload
        : Object.keys(payload)
            .map((key) => `${sentenceCase(key)}: ${payload[key]}`)
            .join('\n');
    openErrorNotification(text);
  }

  throw error;
};

export const refreshPageError = (error: AxiosError): void => {
  if (error.response?.status === 502) {
    const payload = error.response.data;
    const text = `Try to refresh the page. ${payload}`;
    openErrorNotification(text);
  }

  throw error;
};

export const openNotification = (message: React.ReactNode) => {
  appEvents.emit(AppEvents.alertSuccess, [message]);
};

export const openErrorNotification = (message: string) => {
  appEvents.emit(AppEvents.alertError, [message]);
};

export const openWarningNotification = (message: string) => {
  appEvents.emit(AppEvents.alertWarning, [message]);
};

export const getPaths = (obj?: any, parentKey?: string): string[] => {
  let result: any;
  if (isArray(obj)) {
    let idx = 0;
    result = flatMap(obj, (obj) => getPaths(obj, (parentKey || '') + '[' + idx++ + ']'));
  } else if (isPlainObject(obj)) {
    result = flatMap(keys(obj), (key) =>
      map(getPaths(obj[key], key), (subkey) => (parentKey ? parentKey + '.' : '') + subkey)
    );
  } else {
    result = [];
  }
  return concat(result, parentKey || []);
};

export const rateToPercent = (rate: number): string | undefined =>
  isNaN(rate) ? undefined : ((rate - 1) * 100).toFixed(2);

export const getIsMobile = (): boolean => document.documentElement.clientWidth < 900;

export const splitTime = (seconds: number): number[] => {
  let days = 0;
  let hours = 0;
  let mins = 0;
  let secs = seconds;
  if (secs) {
    days = Math.floor(secs / 86400);
    secs -= days * 86400;
    hours = Math.floor(secs / 3600);
    secs -= hours * 3600;
    mins = Math.floor(secs / 60);
    secs -= mins * 60;
  }

  return [days, hours, mins, secs];
};

export const secondsToHumanReadable = (duration: number): string => {
  const [days, hours, mins, secs] = splitTime(duration);

  let timeText = '';

  if (days) {
    timeText += `${days}d`;
  }

  if (hours) {
    timeText += `${hours}h`;
  }

  if (mins) {
    timeText += `${mins}m`;
  }

  if (secs) {
    timeText += `${secs}s`;
  }

  return timeText;
};

export const secondsToHours = (seconds: number) => seconds / 3600;

export const getApiOrigin = () => process.env.REACT_APP_API || '';

export const replaceQueryParams = (params: any) => {
  const query = qs.stringify({
    ...qs.parse(window.location.search),
    ...params,
  });

  window.history.replaceState(null, '', `${window.location.pathname}?${query}${window.location.hash}`);
};
