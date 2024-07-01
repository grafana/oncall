import { PageErrorData } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';

export function initErrorDataState(): Partial<PageErrorData> {
  return { isUnknownError: false, isWrongTeamError: false, wrongTeamNoPermissions: false };
}

export function getWrongTeamResponseInfo(response): Partial<PageErrorData> {
  if (response) {
    if (response.status === 404) {
      return { isNotFoundError: true };
    } else if (response.status === 403 && response.data?.error_code === 'wrong_team') {
      let res = response.data;
      if (res.owner_team) {
        return { isWrongTeamError: true, switchToTeam: { name: res.owner_team.name, id: res.owner_team.id } };
      } else {
        return { isWrongTeamError: true, wrongTeamNoPermissions: true };
      }
    }
  }

  return { isUnknownError: true };
}
