import React, { FC } from 'react';

import QRCodeBase from 'react-qr-code';

import Block from 'components/GBlock/Block';

type Props = {
  value: string;
  className?: string;
};

const QRCode: FC<Props> = (props: Props) => {
  const { value, className = '' } = props;

  return (
    <Block bordered className={className}>
      <QRCodeBase value={value} />
    </Block>
  );
};

export default QRCode;
