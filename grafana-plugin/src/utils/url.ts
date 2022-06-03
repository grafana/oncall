export function getTeamNameSlugFromUrl(): string | undefined {
  const teamName = window.location.pathname.split('/')[2];
  return teamName === 'admin' || teamName === 'auth' ? undefined : teamName;
}

export function getPathnameByTeamNameSlug(teamNameSlug: string): string {
  return window.location.pathname
    .split('/')
    .map((part: string, index) => (index === 2 ? teamNameSlug : part))
    .join('/');
}
