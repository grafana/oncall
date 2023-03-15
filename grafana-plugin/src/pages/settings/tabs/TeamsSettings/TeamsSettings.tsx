import React from 'react';

import { AppRootProps } from '@grafana/data';
import { observer } from 'mobx-react';

import TeamsList from 'containers/TeamsList/TeamsList';
import { withMobXProviderContext } from 'state/withStore';

@observer
class TeamsSettings extends React.Component<AppRootProps> {
  // componentDidMount() {
  //   const { query } = this.props;
  //
  // }

  // componentWillUnmount() {
  //   this.handleChatopsTabChange(undefined);
  // }

  render() {
    return <TeamsList />;
  }
}

export default withMobXProviderContext(TeamsSettings);
