import GrafanaTeamSelect from 'containers/GrafanaTeamSelect/GrafanaTeamSelect';
import React from 'react';

export default function Header({ page }: { page: string }) {
  return  <GrafanaTeamSelect currentPage={page} />
}
