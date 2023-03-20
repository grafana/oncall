import React from 'react';

import { AppRootProps } from '@grafana/data';
import { observer } from 'mobx-react';

import { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import { initErrorDataState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import TeamsList from 'containers/TeamsList/TeamsList';
import { withMobXProviderContext } from 'state/withStore';

interface TeamsSettingsPageState extends PageBaseState {
  showEditTeamsModal: boolean;
}

@observer
class TeamsSettings extends React.Component<AppRootProps, TeamsSettingsPageState> {
  state: TeamsSettingsPageState = {
    showEditTeamsModal: false,
    errorData: initErrorDataState(),
  };

  render() {
    return <TeamsList />;
  }
}

export default withMobXProviderContext(TeamsSettings);
