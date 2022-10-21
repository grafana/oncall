export const getTeamNameSlugFromUrl = (): string | undefined => {
  const teamName = window.location.pathname.split('/')[2];
  return teamName === 'admin' || teamName === 'auth' ? undefined : teamName;
};

export const getPathnameByTeamNameSlug = (teamNameSlug: string): string =>
  window.location.pathname
    .split('/')
    .map((part: string, index) => (index === 2 ? teamNameSlug : part))
    .join('/');
