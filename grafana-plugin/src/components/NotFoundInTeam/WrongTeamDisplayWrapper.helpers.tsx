import { WrongTeamData } from 'components/NotFoundInTeam/WrongTeamDisplayWrapper';

export function getWrongTeamResponseInfo({ response }): Partial<WrongTeamData> {
  if (response) {
    if (response.status === 404) {
      return { notFound: true };
    } else if (response.status === 403 && response.data.error_code === 'wrong_team') {
      let res = response.data;
      if (res.owner_team) {
        return { isError: true, switchToTeam: { name: res.owner_team.name, id: res.owner_team.id } };
      } else {
        return { isError: true, wrongTeamNoPermissions: true };
      }
    }
  }

  return { notFound: true };
}
