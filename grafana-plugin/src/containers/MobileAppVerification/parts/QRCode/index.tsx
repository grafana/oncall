import React, { FC } from 'react';

import QRCodeBase from 'react-qr-code';

import Block from 'components/GBlock/Block';

type Props = {
  value: string;
};

const QRCode: FC<Props> = ({ value }) => (
  <Block bordered>
    <QRCodeBase value={value} />
  </Block>
);

export default QRCode;
