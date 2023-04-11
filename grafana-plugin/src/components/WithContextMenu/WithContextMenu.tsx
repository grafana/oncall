import React, { useEffect, useState } from 'react';

import { ContextMenu } from '@grafana/ui';

export interface WithContextMenuProps {
  children: (props: { openMenu: React.MouseEventHandler<HTMLElement> }) => JSX.Element;
  renderMenuItems: () => React.ReactNode;
  forceIsOpen?: boolean;
  focusOnOpen?: boolean;
}

const query = '[class$="-page-container"] .scrollbar-view';

export const WithContextMenu: React.FC<WithContextMenuProps> = ({
  children,
  renderMenuItems,
  forceIsOpen = false,
  focusOnOpen = true,
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false || forceIsOpen);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    setIsMenuOpen(forceIsOpen);
  }, [forceIsOpen]);

  useEffect(() => {
    const onScrollOrResizeFn = () => setIsMenuOpen(false);
    document.querySelector(query)?.addEventListener('scroll', onScrollOrResizeFn);
    window.addEventListener('resize', onScrollOrResizeFn);

    return () => {
      document.querySelector(query)?.removeEventListener('scroll', onScrollOrResizeFn);
      window.removeEventListener('resize', onScrollOrResizeFn);
    };
  }, []);

  return (
    <>
      {children({
        openMenu: (e) => {
          setIsMenuOpen(true);
          setMenuPosition({
            x: e.pageX,
            y: e.pageY,
          });
        },
      })}

      {isMenuOpen && (
        <ContextMenu
          onClose={() => setIsMenuOpen(false)}
          x={menuPosition.x}
          y={menuPosition.y}
          renderMenuItems={renderMenuItems}
          focusOnOpen={focusOnOpen}
        />
      )}
    </>
  );
};
