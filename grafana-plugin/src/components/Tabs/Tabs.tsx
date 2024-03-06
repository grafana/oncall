import React, { FC, useEffect, useState } from 'react';

import { css } from '@emotion/css';
import { Tab, TabsBar, TabContent, useStyles2 } from '@grafana/ui';
import cn from 'classnames';

import { LocationHelper } from 'utils/LocationHelper';

interface TabConfig {
  label: string;
  content: React.ReactNode;
}

interface TabsProps {
  tabs: TabConfig[];
  tabContentClassName?: string;
  shouldBeSyncedWithQueryString?: boolean;
  // in case there are more than 1 <Tabs /> in the page, we want to use different queryString keys
  queryStringKey?: string;
}

export const Tabs: FC<TabsProps> = ({
  tabs,
  tabContentClassName,
  shouldBeSyncedWithQueryString = true,
  queryStringKey = 'activeTab',
}) => {
  const styles = useStyles2(getStyles);

  const defaultActiveLabel =
    (shouldBeSyncedWithQueryString && LocationHelper.getQueryParam(queryStringKey)) || tabs[0].label;
  const [activeTabLabel, setActiveTabLabel] = useState(defaultActiveLabel);

  const setLabel = (label: string) => {
    setActiveTabLabel(label);
    if (shouldBeSyncedWithQueryString) {
      LocationHelper.update({ [queryStringKey]: label }, 'partial');
    }
  };

  useEffect(
    () => () => {
      if (shouldBeSyncedWithQueryString) {
        LocationHelper.update({ [queryStringKey]: undefined }, 'partial');
      }
    },
    []
  );

  return (
    <>
      <TabsBar>
        {tabs.map(({ label }) => (
          <Tab label={label} key={label} onChangeTab={() => setLabel(label)} active={activeTabLabel === label} />
        ))}
      </TabsBar>
      <TabContent className={cn(styles.content, tabContentClassName)}>
        {tabs.find(({ label }) => label === activeTabLabel)?.content}
      </TabContent>
    </>
  );
};

export const getStyles = () => ({
  content: css({
    marginTop: '16px',
  }),
});
