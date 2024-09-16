import React, { FC } from 'react';

import { css } from '@emotion/css';
import { Stack, useStyles2 } from '@grafana/ui';
import { StackSize } from 'helpers/consts';

import AppleLogoSVG from 'assets/img/apple-logo.svg';
import PlayStoreLogoSVG from 'assets/img/play-store-logo.svg';
import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';

export const DownloadIcons: FC = () => {
  const styles = useStyles2(getStyles);

  return (
    <Stack direction="column" gap={StackSize.lg}>
      <Text type="primary" strong>
        Download
      </Text>
      <Text type="primary">The Grafana OnCall app is available on both the App Store and Google Play Store.</Text>
      <Stack direction="column">
        <a
          style={{ width: '100%' }}
          href="https://apps.apple.com/us/app/grafana-oncall-preview/id1669759048"
          target="_blank"
          rel="noreferrer"
        >
          <Block hover fullWidth withBackground bordered className={styles.iconBlock}>
            <img src={AppleLogoSVG} alt="Apple" className={styles.icon} />
            <Text type="primary" className={styles.iconText}>
              iOS
            </Text>
          </Block>
        </a>
        <a
          style={{ width: '100%' }}
          href="https://play.google.com/store/apps/details?id=com.grafana.oncall.prod"
          target="_blank"
          rel="noreferrer"
        >
          <Block hover fullWidth bordered className={styles.iconBlock}>
            <img src={PlayStoreLogoSVG} alt="Play Store" className={styles.icon} />
            <Text type="primary" className={styles.iconText}>
              Android
            </Text>
          </Block>
        </a>
      </Stack>
    </Stack>
  );
};

const getStyles = () => {
  return {
    icon: css`
      width: 48px;
      height: 48px;
      cursor: default;
    `,

    iconBlock: css`
      display: flex;
      align-items: center;
      min-height: 80px;
      column-gap: 12px;
    `,

    iconText: css`
      margin-left: 16px;
      cursor: default;
    `,

    iconTag: css`
      border-radius: 12px;
      font-size: 12px;
      padding: 2px 8px;
      cursor: default;
    `,
  };
};
