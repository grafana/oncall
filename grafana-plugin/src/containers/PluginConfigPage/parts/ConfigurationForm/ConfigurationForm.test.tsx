import React from 'react';

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import PluginState from 'state/plugin';
import { ONCALL_API_URL_LOCAL_STORAGE_KEY } from 'utils/localStorage';

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
  const user = userEvent.setup();
  const component = render(<ConfigurationForm onSuccessfulSetup={mockOnSuccessfulSetup} />);

  // fill out onCallApiUrl input
  await user.click(screen.getByTestId('onCallApiUrl'));
  await user.keyboard(onCallApiUrl);

  // submit form
  await user.click(screen.getByRole('button'));

  return { dom: component.baseElement, mockOnSuccessfulSetup };
};

describe('ConfigurationForm', () => {
  afterEach(() => {
    jest.resetAllMocks();
    localStorage.clear();
  });

  test('It calls the onSuccessfulSetup callback on successful form submission', async () => {
    const { mockOnSuccessfulSetup } = await fillOutFormAndTryToSubmit(VALID_ONCALL_API_URL);

    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledTimes(1);
    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledWith(VALID_ONCALL_API_URL);
    expect(mockOnSuccessfulSetup).toHaveBeenCalledTimes(1);
  });

  test("It doesn't allow the user to submit if the URL is invalid", async () => {
    const { dom, mockOnSuccessfulSetup } = await fillOutFormAndTryToSubmit('potato');

    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledTimes(0);
    expect(mockOnSuccessfulSetup).toHaveBeenCalledTimes(0);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(dom).toMatchSnapshot();
  });

  test('It saves the OnCall API URL to localStorage when the self hosted plugin API call is successful', async () => {
    await fillOutFormAndTryToSubmit(VALID_ONCALL_API_URL);
    expect(localStorage.getItem(ONCALL_API_URL_LOCAL_STORAGE_KEY)).toEqual(JSON.stringify(VALID_ONCALL_API_URL));
  });

  test("It doesn't save the OnCall API URL to localStorage when if the self hosted plugin API call is not successful", async () => {
    await fillOutFormAndTryToSubmit(VALID_ONCALL_API_URL, false);
    expect(localStorage.getItem(ONCALL_API_URL_LOCAL_STORAGE_KEY)).toBeNull();
  });

  test('It shows an error message if the self hosted plugin API call fails', async () => {
    const { dom, mockOnSuccessfulSetup } = await fillOutFormAndTryToSubmit(VALID_ONCALL_API_URL, false);

    expect(PluginState.selfHostedInstallPlugin).toHaveBeenCalledWith(VALID_ONCALL_API_URL);
    expect(mockOnSuccessfulSetup).toHaveBeenCalledTimes(0);
    expect(dom).toMatchSnapshot();
  });
});
