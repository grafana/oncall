import PageErrorHandlingWrapper, { PageBaseState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper';
import { initErrorDataState } from 'components/PageErrorHandlingWrapper/PageErrorHandlingWrapper.helpers';
import React from 'react';
import { RouteComponentProps, withRouter } from 'react-router-dom';
import { PageProps, WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

interface Integration2Props extends WithStoreProps, PageProps, RouteComponentProps {}

interface Integration2State extends PageBaseState {}

class Integration2 extends React.Component<Integration2Props, Integration2State> {
  constructor(props: Integration2Props) {
    super(props);

    this.state = {
      errorData: initErrorDataState(),
    };
  }

  render() {
    const { errorData } = this.state;

    return (
      <PageErrorHandlingWrapper errorData={errorData} objectName="integration" pageName="Integration">
        {() => <div></div>}
      </PageErrorHandlingWrapper>
    );
  }
}

export default withRouter(withMobXProviderContext(Integration2));
