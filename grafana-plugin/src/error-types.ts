/**
 * This one would automatically show notification in top right corner with proper icon and color according to severity.
 * It optionally might have title. Description is required.
 */
type GlobalNotificationError = {
  type: 'global-notification';
  severity: 'error' | 'warning';
  title?: string;
  description: string;
};

/**
 * This one can be used to conditionally show inline banner in any place on UI.
 */
type InlineBannerError = {
  type: 'inline-banner';
  severity: 'error' | 'warning';
  title?: string;
  description: string;
};

/**
 * This one can be used to redirect user to a specific URL.
 */
type RedirectError = {
  type: 'redirect';
  path: string;
};

/**
 * This one is used to show form validation errors. Keys in fields should match the names of fields in form
 * so that they can be easily mapped to react-hook-form errors and properly show below each form field.
 */
type FormError = {
  type: 'form';
  fields: Record<string, string[]>;
};

/**
 * This one is used just to log error in the console but they wouldn't be shown in UI.
 */
type ImplicitError = {
  type: 'implicit';
  message: string;
};

type OnCallError = GlobalNotificationError | InlineBannerError | RedirectError | FormError | ImplicitError;

/**
 * Unsuccessful HTTP response can be a mix of any of the errors above. For example you might want to
 * show inline form validation errors and at the same time global notification.
 */
type OnCallUnsuccessfulHttpResponse = OnCallError[];

const GlobalNotificationErrorExample: OnCallUnsuccessfulHttpResponse = [
  {
    type: 'global-notification',
    severity: 'error',
    title: 'Webhook creation failed',
    description: 'You already have another webhook with the same name.',
  },
];

const InlineBannerErrorExample: OnCallUnsuccessfulHttpResponse = [
  {
    type: 'inline-banner',
    severity: 'warning',
    title: 'Inline banner title',
    description: 'Inline banner description',
  },
];

const FormErrorExample: OnCallUnsuccessfulHttpResponse = [
  {
    type: 'form',
    fields: {
      name: ['Ensure this field has no more than 100 characters.', 'Name cannot include special characters.'],
      url: ['This field is required'],
    },
  },
];

const ImplicitErrorExample: OnCallUnsuccessfulHttpResponse = [
  {
    type: 'implicit',
    message: 'Error message',
  },
];

const MixedErrorExample: OnCallUnsuccessfulHttpResponse = [
  {
    type: 'global-notification',
    severity: 'error',
    title: 'Webook cannot be created',
    description: 'Your form includes invalid data.',
  },
  {
    type: 'form',
    fields: {
      name: ['Ensure this field has no more than 100 characters.', 'Name cannot include special characters.'],
      url: ['This field is required'],
    },
  },
];

const MixedErrorExample2: OnCallUnsuccessfulHttpResponse = [
  {
    type: 'redirect',
    path: '/plugins/grafana-oncall-app/configure',
  },
  {
    type: 'inline-banner',
    severity: 'warning',
    title: 'Invalid OnCall API URL',
    description: 'Make sure your OnCall API URL is correct and retest connection.',
  },
];
