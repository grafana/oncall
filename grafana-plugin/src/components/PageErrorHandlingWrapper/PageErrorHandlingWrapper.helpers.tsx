import { PageErrorData } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';

export const initErrorDataState = (): Partial<PageErrorData> => ({
  isWrongTeamError: false,
  wrongTeamNoPermissions: false,
});

export const getWrongTeamResponseInfo = ({ response }): Partial<PageErrorData> => {
  if (response) {
    const { status, data } = response;

    if (status === 404) {
      return { isNotFoundError: true };
    } else if (status === 403 && data.error_code === 'wrong_team') {
      const { owner_team } = data;
      if (owner_team) {
        return { isWrongTeamError: true, switchToTeam: { name: owner_team.name, id: owner_team.id } };
      } else {
        return { isWrongTeamError: true, wrongTeamNoPermissions: true };
      }
    }
  }

  return { isNotFoundError: true };
};
