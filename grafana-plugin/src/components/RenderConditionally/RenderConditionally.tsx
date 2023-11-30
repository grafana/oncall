import React, { FC, ReactNode } from 'react';

interface RenderConditionallyProps {
  shouldRender?: boolean;
  children: ReactNode;
  backupChildren?: ReactNode;
}

const RenderConditionally: FC<RenderConditionallyProps> = ({ shouldRender, children, backupChildren = null }) =>
  shouldRender ? <>{children}</> : <>{backupChildren}</>;

export default RenderConditionally;
