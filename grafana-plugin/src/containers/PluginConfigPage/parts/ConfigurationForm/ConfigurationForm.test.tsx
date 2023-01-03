import React from 'react';

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import PluginState from 'state/plugin';

import ConfigurationForm from '.';

jest.mock('state/plugin');

const VALID_ONCALL_API_URL = 'http://host.docker.internal:8080';
const SELF_HOSTED_PLUGIN_API_ERROR_MSG = 'ohhh nooo there was an error from the OnCall API';

const fillOutFormAndTryToSubmit = async (onCallApiUrl: string, selfHostedInstallPluginSuccess = true) => {
  // mocks
  const mockOnSuccessfulSetup = jest.fn();
  PluginState.selfHostedInstallPlugin = jest
    .fn()
    .mockResolvedValueOnce(selfHostedInstallPluginSuccess ? null : SELF_HOSTED_PLUGIN_API_ERROR_MSG);

  // setup
  const component = render(
    <ConfigurationForm onSuccessfulSetup={mockOnSuccessfulSetup} defaultOnCallApiUrl="http://potato.com" />
  );

  // fill out onCallApiUrl input
  const input = screen.getByTestId('onCallApiUrl');

  await userEvent.click(input);
  await userEvent.clear(input); // clear the input first before typing to wipe out the placeholder text
  await userEvent.keyboard(onCallApiUrl);

  // submit form
  await userEvent.click(screen.getByRole('button'));

  return { dom: component.baseElement, mockOnSuccessfulSetup };
};

describe('ConfigurationForm', () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  test('it sets the default input value of onCallApiUrl to the passed in prop value of defaultOnCallApiUrl', () => {
    const processEnvOnCallApiUrl = 'http://hello.com';
    render(<ConfigurationForm onSuccessfulSetup={jest.fn()} defaultOnCallApiUrl={processEnvOnCallApiUrl} />);
    expect(screen.getByDisplayValue(processEnvOnCallApiUrl)).toBeInTheDocument();
  });

  test('It calls the onSuccessfulSetup callback on successful form submission', async () => {
    const { mockOnSuccessfulSetup } = await fillOutFormAndTryToSubmit(VALID_ONCALL_API_URL);

    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledWith(VALID_ONCALL_API_URL, false);
    expect(mockOnSuccessfulSetup).toHaveBeenCalledTimes(1);
  });

  test("It doesn't allow the user to submit if the URL is invalid", async () => {
    const { dom, mockOnSuccessfulSetup } = await fillOutFormAndTryToSubmit('potato');

    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledTimes(0);
    expect(mockOnSuccessfulSetup).toHaveBeenCalledTimes(0);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(dom).toMatchSnapshot();
  });

  test('It shows an error message if the self hosted plugin API call fails', async () => {
    const { dom, mockOnSuccessfulSetup } = await fillOutFormAndTryToSubmit(VALID_ONCALL_API_URL, false);

    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledWith(VALID_ONCALL_API_URL, false);
    expect(mockOnSuccessfulSetup).toHaveBeenCalledTimes(0);
    expect(dom).toMatchSnapshot();
  });
});
