const OnCallErrorCode = {
  // 1 - 999 reserved for engine errors
  CANNOT_CREATE_INTEGRATION: 1,
  CANNOT_CREATE_SCHEDULE: 2,
  CANNOT_RETRIEVE_USER: 3,
  SERVICE_ACCOUNT_TOKEN_INVALID: 4,
  ONCALL_API_TOKEN_INVALID: 5,
  // ...

  // 1000 - 1999 reserved for backend plugin proxy errors
  // ...
} as const;
type OnCallErrorCode = (typeof OnCallErrorCode)[keyof typeof OnCallErrorCode];

type OnCallError = {
  code?: OnCallErrorCode;
  message: string;
  fields?: {
    [key: string]: string[];
  };
};

// Unsuccessful HTTP response can be a mix of any of the errors above

type OnCallUnsuccessfulHttpResponse = OnCallError[];

const ErrorExample1: OnCallUnsuccessfulHttpResponse = [
  {
    code: 1,
    message: 'Cannot create integration',
    fields: {
      name: ['Ensure this field has no more than 100 characters.', 'Name cannot include special characters.'],
      url: ['This field is required'],
    },
  },
];

const ErrorExample2: OnCallUnsuccessfulHttpResponse = [
  {
    code: 2,
    message: 'Cannot create schedule',
    details: 'Schedule with the same name already exists',
  },
];

const ErrorExample3: OnCallUnsuccessfulHttpResponse = [
  {
    code: 3,
    message: 'Cannot retrieve user',
  },
  {
    code: 4,
    message: 'OnCall API token invalid',
  },
];
