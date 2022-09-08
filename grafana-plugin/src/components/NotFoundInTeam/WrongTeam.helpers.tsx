interface WrongTeamResponse {
  notFound?: boolean;
  wrongTeamError?: boolean;
  teamToSwitch?: { name: string; id: string };
  wrongTeamNoPermissions?: boolean;
}

export function getWrongTeamResponseInfo({ response }): WrongTeamResponse {
  if (response) {
    if (response.status === 404) {
      return { notFound: true };
    } else if (response.status === 403 && response.data.error_code === 'wrong_team') {
      let res = response.data;
      if (res.owner_team) {
        return { wrongTeamError: true, teamToSwitch: { name: res.owner_team.name, id: res.owner_team.id } };
      } else {
        return { wrongTeamError: true, wrongTeamNoPermissions: true };
      }
    }
  }

  return { notFound: true };
}
