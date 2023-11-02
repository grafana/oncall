import React, { useRef } from 'react';

interface CustomContextMenuDisplayProps {
  openMenu: React.MouseEventHandler<HTMLElement>;
  listWidth: number;
  listBorder: number;
  stopPropagation?: boolean;
  withBackground?: boolean;
  baseClassName?: string;
  extraClassName?: string;
  children: React.ReactNode;
}

const CustomContextMenuDisplay: React.FC<CustomContextMenuDisplayProps> = (props) => {
  const ref = useRef<HTMLDivElement>();
  const {
    openMenu,
    children,
    listWidth,
    listBorder,
    withBackground,
    baseClassName,
    extraClassName,
    stopPropagation = false,
  } = props;

  return (
    <div
      ref={ref}
      className={[baseClassName, { [`${baseClassName}--withBackground`]: withBackground }, extraClassName].join(' ')}
      onClick={(e) => {
        if (stopPropagation) {
          e.stopPropagation();
        }

        const boundingRect = ref.current.getBoundingClientRect();

        openMenu({
          pageX: boundingRect.right - listWidth + listBorder * 2,
          pageY: boundingRect.top + boundingRect.height,
        } as any);
      }}
    >
      {children}
    </div>
  );
};

export default CustomContextMenuDisplay;
