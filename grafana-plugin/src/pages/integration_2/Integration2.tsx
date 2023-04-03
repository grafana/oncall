import React from 'react';

import { HorizontalGroup, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';
import { RouteComponentProps, withRouter } from 'react-router-dom';

import InfoBadge from 'components/InfoBadge/InfoBadge';
import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import { initErrorDataState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import styles from './Integration2.module.scss';

const cx = cn.bind(styles);

interface Integration2Props extends WithStoreProps, PageProps, RouteComponentProps<{ id: string }> {}

interface Integration2State extends PageBaseState {}

@observer
class Integration2 extends React.Component<Integration2Props, Integration2State> {
  constructor(props: Integration2Props) {
    super(props);

    this.state = {
      errorData: initErrorDataState(),
    };
  }

  async componentDidMount() {
    await this.loadIntegration();
  }

  render() {
    const { errorData } = this.state;
    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    const integration = store.alertReceiveChannelStore.items[id];
    const { isNotFoundError, isWrongTeamError } = errorData;

    if (!integration && !isNotFoundError && !isWrongTeamError) {
      return (
        <div className={cx('root')}>
          <LoadingPlaceholder text="Loading Integration..." />
        </div>
      );
    }

    return (
      <PageErrorHandlingWrapper errorData={errorData} objectName="integration" pageName="Integration">
        {() => (
          <div className={cx('root')}>
            <div className={cx('integration__heading')}>
              <h1 className={cx('integration__name')}>
                <Emoji text={integration.verbal_name} />
              </h1>
              {integration.description && <p className={cx('integration__description')}>{integration.description}</p>}
              <HorizontalGroup>
                <InfoBadge borderType="primary" count={'0/0'} tooltipTitle="0/0 Alert Groups" tooltipContent={<></>} />
                <InfoBadge
                  borderType="success"
                  icon="link"
                  count={'1'}
                  tooltipTitle="1 Escalation Chain"
                  tooltipContent={<></>}
                />
                <InfoBadge
                  borderType="warning"
                  icon="exclamation-triangle"
                  count={'1'}
                  tooltipTitle="1 Warning"
                  tooltipContent={<></>}
                />
              </HorizontalGroup>
            </div>
            <div className={cx('integration__content')}></div>
          </div>
        )}
      </PageErrorHandlingWrapper>
    );
  }

  async loadIntegration() {
    const {
      store,
      match: {
        params: { id },
      },
    } = this.props;

    return new Promise(async (resolve) => {
      if (!store.alertReceiveChannelStore.items[id]) {
        // See what happens if the request fails
        await store.alertReceiveChannelStore.loadItem(id);
      }

      resolve(store.alertReceiveChannelStore.items[id]);
    });
  }
}

export default withRouter(withMobXProviderContext(Integration2));
