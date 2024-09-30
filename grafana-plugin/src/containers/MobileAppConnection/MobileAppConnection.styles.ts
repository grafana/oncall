import { css } from '@emotion/css';
import { Colors } from 'styles/utils.styles';

export const getMobileAppConnectionStyles = () => {
  return {
    container: css`
      display: flex;
      flex-direction: row;
      min-width: 100%;

      @media (max-width: 768px) {
        flex-direction: column;
      }
    `,

    containerBox: css`
      flex-basis: 50%;

      &:first-child {
        margin-right: 8px;
      }
      *:last-child {
        margin-left: 8px;
      }

      @media (max-width: 768px) {
        &:first-child {
          margin-right: 0px;
          margin-bottom: 8px;
        }
        &:last-child {
          margin-left: 0px;
          margin-top: 8px;
        }
      }
    `,

    notificationButtons: css`
      width: 100%;
      padding-top: 12px;
    `,

    icon: css`
      margin-top: -6px;
      margin-left: 4px;
      fill: ${Colors.GREEN_6};
    `,

    disconnectContainer: css`
      position: relative;
      display: flex;
      justify-content: center;
      width: 100%;
    `,
    disconnectQRCode: css`
      width: 240px;
      height: auto;
      filter: blur(6px);
      opacity: 0.6;
    `,

    blurry: css`
      filter: blur(4px);
      opacity: 0.2;
    `,

    qrCode: css`
      background-color: #fff;
      margin-bottom: 12px;
    `,

    qrLoader: css`
      position: absolute;
      z-index: 10;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;

      i {
        font-size: 32px;
      }
    `,

    qrLoaderText: css`
      text-align: center;
      margin-bottom: 12px;
      display: block;
    `,
  };
};
