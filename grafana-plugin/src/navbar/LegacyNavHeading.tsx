import { isTopNavbar } from 'plugin/GrafanaPluginRootPage.helpers';

interface LegacyNavHeadingProps {
  children: JSX.Element;
  show?: boolean;
}

export default function LegacyNavHeading(props: LegacyNavHeadingProps): JSX.Element {
  const { show = !isTopNavbar(), children } = props;

  if (!show) {
    return null;
  }
  return children;
}
