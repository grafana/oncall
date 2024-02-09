import React from 'react';

import { IconName, Tab, TabsBar } from '@grafana/ui';
import cn from 'classnames/bind';

import { pages } from 'pages/pages';
import { useStore } from 'state/useStore';

import styles from './LegacyNavTabsBar.module.scss';

const cx = cn.bind(styles);

export const LegacyNavTabsBar = function ({ currentPage }: { currentPage: string }): JSX.Element {
  const store = useStore();

  const navigationPages = Object.keys(pages)
    .map((page) => pages[page])
    .filter((page) => (page.hideFromTabsFn ? !page.hideFromTabsFn(store) : !page.hideFromTabs));

  return (
    <div className={cx('root')}>
      <TabsBar>
        {navigationPages.map((page, index) => (
          <Tab
            key={index}
            icon={page.icon as IconName}
            label={page.text}
            href={page.path}
            active={
              currentPage === page.id ||
              (currentPage === 'schedule' && page.id === 'schedules') ||
              (currentPage === 'incident' && page.id === 'incidents')
            }
          />
        ))}
      </TabsBar>
    </div>
  );
};
