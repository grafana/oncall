import React from 'react';

import { Button } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { WithPermissionControl } from 'containers/WithPermissionControl2/WithPermissionControl';
import { UserAction } from 'state/userAction';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Test.module.css';

const cx = cn.bind(styles);

@observer
class Test extends React.Component<any, any> {
  render() {
    return (
      <div className={cx('root')}>
        <WithPermissionControl userAction={UserAction.UpdateSchedules}>
          {(disabled) => <Button disabled={disabled}>Click me!</Button>}
        </WithPermissionControl>
      </div>
    );
  }
}

export default withMobXProviderContext(Test);
