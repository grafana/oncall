import React, { FC } from 'react';

import { QRCodeSVG } from 'qrcode.react';

import { Block } from 'components/GBlock/Block';

type Props = {
  value: string;
  className?: string;
};

export const QRCode: FC<Props> = (props: Props) => {
  const { value, className = '' } = props;

  return (
    <Block bordered className={className}>
      <QRCodeSVG value={value} size={256} />
    </Block>
  );
};
