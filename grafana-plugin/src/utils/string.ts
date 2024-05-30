// Truncate a string to a given maximum length, adding ellipsis if it was truncated.
export function truncateTitle(title: string, length: number): string {
  if (title.length <= length) {
    return title;
  }
  const part = title.slice(0, length - 3);
  return `${part.trimEnd()}...`;
}

export const formatSourceCodeJsonString = (data: string) => {
  try {
    const jsonValue = JSON.parse(data);
    return JSON.stringify(jsonValue, null, 4);
  } catch (e) {
    return data;
  }
};

export const safeJSONStringify = (value: unknown) => {
  try {
    return JSON.stringify(value);
  } catch (_err) {
    return value;
  }
};

export const VALID_URL_PATTERN = /(http|https)\:\/\/.+?\..+/;
