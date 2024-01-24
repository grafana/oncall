import React, { FC } from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';

import HamburgerMenu from 'components/HamburgerMenu/HamburgerMenu';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';

interface HamburgerContextMenuProps {
  items: Array<React.ReactNode | 'divider'>;
  hamburgerIconClassName?: string;
}

const HamburgerContextMenu: FC<HamburgerContextMenuProps> = ({ items, hamburgerIconClassName }) => {
  const styles = useStyles2(getStyles);

  return (
    <WithContextMenu
      renderMenuItems={() => (
        <div className={styles.menuList}>
          {items.map((item, idx) =>
            item === 'divider' ? (
              <div key="line-break" className="thin-line-break" />
            ) : (
              <div className={styles.menuItem} key={idx}>
                {item}
              </div>
            )
          )}
        </div>
      )}
    >
      {({ openMenu }) => (
        <HamburgerMenu openMenu={openMenu} listBorder={2} listWidth={225} className={hamburgerIconClassName} />
      )}
    </WithContextMenu>
  );
};

export const getStyles = (theme: GrafanaTheme2) => ({
  menuList: css({
    display: 'flex',
    flexDirection: 'column',
    width: '225px',
    borderRadius: '2px',
  }),
  menuItem: css({
    padding: '8px',
    whiteSpace: 'nowrap',
    borderLeft: '2px solid transparent',
    minWidth: '84px',
    gap: '8px',
    cursor: 'pointer',
    '&:hover': {
      background: theme.colors.background.secondary,
    },
  }),
});

export default HamburgerContextMenu;
