import React, { FC, ReactNode } from 'react';

interface RenderConditionallyProps {
  shouldRender?: boolean;
  children?: ReactNode;
  render?: () => ReactNode;
  backupChildren?: ReactNode;
}

export const RenderConditionally: FC<RenderConditionallyProps> = ({
  shouldRender,
  children,
  render,
  backupChildren = null,
}) => {
  if (render) {
    return shouldRender ? <>{render()}</> : <>{backupChildren}</>;
  }

  return shouldRender ? <>{children}</> : <>{backupChildren}</>;
};
