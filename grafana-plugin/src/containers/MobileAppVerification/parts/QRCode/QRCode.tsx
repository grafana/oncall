import React, { FC } from 'react';

import QRCodeBase from 'react-qr-code';

import Block from 'components/GBlock/Block';

type Props = {
  value: string;
  className: string;
};

const QRCode: FC<Props> = ({ value, className }) => (
  <Block bordered className={className}>
    <QRCodeBase value={value} />
  </Block>
);

export default QRCode;
