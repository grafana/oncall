import React, { FC, ReactNode } from 'react';

interface RenderConditionallyProps {
  shouldRender?: boolean;
  children: ReactNode;
}

const RenderConditionally: FC<RenderConditionallyProps> = ({ shouldRender, children }) =>
  shouldRender ? <>{children}</> : null;

export default RenderConditionally;
