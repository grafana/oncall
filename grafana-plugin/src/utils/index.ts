import { AppEvents } from '@grafana/data';
import { AxiosError } from 'axios';
import { sentenceCase } from 'change-case';
// @ts-ignore
import appEvents from 'grafana/app/core/app_events';
import { isArray, concat, isPlainObject, flatMap, map, keys } from 'lodash-es';
import qs from 'query-string';

import { isNetworkError } from 'network';

export class KeyValuePair<T = string | number> {
  key: T;
  value: string;

  constructor(key: T, value: string) {
    this.key = key;
    this.value = value;
  }
}

export const TZ_OFFSET = new Date().getTimezoneOffset();

export const getTzOffsetHours = (): number => {
  return TZ_OFFSET / 60;
};

export function showApiError(error: any) {
  if (isNetworkError(error) && error.response && error.response.status >= 400 && error.response.status < 500) {
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
}

export function refreshPageError(error: AxiosError) {
  if (isNetworkError(error) && error.response?.status === 502) {
    const payload = error.response.data;
    const text = `Try to refresh the page. ${payload}`;
    openErrorNotification(text);
  }

  throw error;
}

export function throttlingError(error: AxiosError) {
  if (isNetworkError(error) && error.response?.status === 429) {
    const seconds = Number(error.response?.headers['retry-after']);
    const minutes = Math.floor(seconds / 60);
    const text =
      'Too many requests, please try again in ' +
      (minutes > 0 ? `${Math.floor(seconds / 60)} minutes.` : `${seconds} seconds.`);
    openErrorNotification(text);
  } else {
    if (error.response?.data === '') {
      openErrorNotification(
        'Grafana OnCall is unable to verify your phone number due to incorrect number or verification service being unavailable.'
      );
    } else {
      openErrorNotification(error.response?.data);
    }
  }
}

export function openNotification(message: React.ReactNode) {
  appEvents.emit(AppEvents.alertSuccess, [message]);
}

export function openErrorNotification(message: string) {
  appEvents.emit(AppEvents.alertError, [message]);
}

export function openWarningNotification(message: string) {
  appEvents.emit(AppEvents.alertWarning, [message]);
}

export function getPaths(obj?: any, parentKey?: string): string[] {
  let result: any;
  if (isArray(obj)) {
    let idx = 0;
    result = flatMap(obj, function (obj) {
      return getPaths(obj, (parentKey || '') + '[' + idx++ + ']');
    });
  } else if (isPlainObject(obj)) {
    result = flatMap(keys(obj), function (key) {
      return map(getPaths(obj[key], key), function (subkey) {
        return (parentKey ? parentKey + '.' : '') + subkey;
      });
    });
  } else {
    result = [];
  }
  return concat(result, parentKey || []);
}

export function rateToPercent(rate: number): string | undefined {
  if (isNaN(rate)) {
    return undefined;
  }
  return ((rate - 1) * 100).toFixed(2);
}

export function getIsMobile(): boolean {
  const width = document.documentElement.clientWidth;
  return width < 900;
}

export function splitTime(seconds: number): number[] {
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
}

export function secondsToHumanReadable(duration: number): string {
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
}

export function secondsToHours(seconds: number) {
  return seconds / 3600;
}

export function getApiOrigin() {
  return process.env.REACT_APP_API || '';
}

export function replaceQueryParams(params: any) {
  const query = qs.stringify({
    ...qs.parse(window.location.search),
    ...params,
  });

  window.history.replaceState(null, '', `${window.location.pathname}?${query}${window.location.hash}`);
}
