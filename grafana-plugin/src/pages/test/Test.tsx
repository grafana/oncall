import React from 'react';

import { Button } from '@grafana/ui';
import { PluginPage } from 'PluginPage';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { WithPermissionControl } from 'containers/WithPermissionControl2/WithPermissionControl';
import { withMobXProviderContext } from 'state/withStore';
import { UserActions } from 'utils/authorization';

import styles from './Test.module.css';

const cx = cn.bind(styles);

@observer
class Test extends React.Component<any, any> {
  render() {
    return (
      <PluginPage>
        <div className={cx('root')}>
          <WithPermissionControl userAction={UserActions.SchedulesWrite}>
            {(disabled) => <Button disabled={disabled}>Click me!</Button>}
          </WithPermissionControl>
        </div>
      </PluginPage>
    );
  }
}

export default withMobXProviderContext(Test);
