import React, { useEffect, useRef, useState } from 'react';

import { Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from 'assets/style/utils.css';
import { TEXT_ELLIPSIS_CLASS } from 'utils/consts';

const cx = cn.bind(styles);

interface TextEllipsisTooltipProps {
  content: string;
  queryClassName?: string;
  placement?: string;
  className?: string;
  children: JSX.Element | JSX.Element[];
}

const TextEllipsisTooltip: React.FC<TextEllipsisTooltipProps> = ({
  queryClassName = TEXT_ELLIPSIS_CLASS,
  className,
  content: textContent,
  placement,
  children,
}) => {
  const [isEllipsis, setIsEllipsis] = useState(true);
  const elContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setEllipsis();
  }, []);

  const elContent = (
    <div className={cx(className)} ref={elContentRef} onMouseOver={setEllipsis}>
      {children}
    </div>
  );

  if (isEllipsis) {
    return (
      <Tooltip content={textContent} placement={placement as any}>
        {/* The wrapping div is needed, otherwise the attached ref will be lost when <Tooltip /> mounts */}
        <div>{elContent}</div>
      </Tooltip>
    );
  }

  return elContent;

  function setEllipsis() {
    const el = elContentRef?.current?.querySelector<HTMLElement>(`.${queryClassName}`);
    if (!el) {
      return;
    }

    setIsEllipsis(el.offsetHeight < el.scrollHeight);
  }
};

export default TextEllipsisTooltip;
