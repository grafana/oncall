// Truncate a string to a given maximum length, adding ellipsis if it was truncated.
export function truncateTitle(title: string, length: number): string {
  if (title.length < length) {
    return title;
  }
  const part = title.slice(0, length - 3);
  return `${part.trimEnd()}...`;
}
