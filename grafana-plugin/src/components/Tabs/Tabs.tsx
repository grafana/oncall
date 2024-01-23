import React, { FC, useState } from 'react';

import { css } from '@emotion/css';
import { Tab, TabsBar, TabContent, useStyles2 } from '@grafana/ui';
import LocationHelper from 'utils/LocationHelper';
import cn from 'classnames';

interface TabConfig {
  label: string;
  content: React.ReactNode;
}

interface TabsProps {
  tabs: TabConfig[];
  tabContentClassName?: string;
  shouldBeSyncedWithQueryString?: boolean;
}

const Tabs: FC<TabsProps> = ({ tabs, tabContentClassName, shouldBeSyncedWithQueryString = true }) => {
  const styles = useStyles2(getStyles);

  const defaultActiveLabel =
    (shouldBeSyncedWithQueryString && LocationHelper.getQueryParams('activeTab')) || tabs[0].label;
  const [activeTabLabel, setActiveTabLabel] = useState(defaultActiveLabel);

  const setLabel = (label: string) => {
    setActiveTabLabel(label);
    if (shouldBeSyncedWithQueryString) {
      LocationHelper.update({ activeTab: label }, 'partial');
    }
  };

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

export default Tabs;
