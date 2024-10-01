interface LegacyNavHeadingProps {
  children: JSX.Element;
  show?: boolean;
}

export const LegacyNavHeading = function (props: LegacyNavHeadingProps): JSX.Element {
  const { show = false, children } = props;
  return show ? children : null;
};
