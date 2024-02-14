import React, { FC, useState } from 'react';

import { css } from '@emotion/css';
import { Tab, TabsBar, TabContent, useStyles2 } from '@grafana/ui';
import cn from 'classnames';

interface TabConfig {
  label: string;
  content: React.ReactNode;
}

interface TabsProps {
  tabs: TabConfig[];
  defaultActiveLabel?: string;
  tabContentClassName?: string;
}

export const Tabs: FC<TabsProps> = ({ tabs, defaultActiveLabel, tabContentClassName }) => {
  const styles = useStyles2(getStyles);
  const [activeTabLabel, setActiveTabLabel] = useState(defaultActiveLabel || tabs[0].label);

  return (
    <>
      <TabsBar>
        {tabs.map(({ label }) => (
          <Tab
            label={label}
            key={label}
            onChangeTab={() => setActiveTabLabel(label)}
            active={activeTabLabel === label}
          />
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
