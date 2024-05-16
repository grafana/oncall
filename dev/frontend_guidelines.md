# OnCall Frontend Guidelines

The base guidelines we decided to follow are:

- <https://github.com/ryanmcdermott/clean-code-javascript>
- <https://github.com/grafana/grafana/tree/main/contribute/style-guides>

Anything that is either not covered by the materials above or we decided to do differently is stated in this document.

## Ways of working

### Code reviews

- PR can be merged when the following conditions are met:
  - CI pipeline succeeded without bypassing checks
  - There is at least 1 approval from the frontend team and no opened remarks from reviewers other than the approver
  - All comments are replied, answered, addressed or discussed separately
  - We make use of builtin GH PR reviews
  - Minor comments that don’t need to be addressed right away and are not a blocker for a merge
are marked with “Minor: “ prefix
  - *Unless there is some important hotfix to make and no frontend mates are available*

## Technical conventions

### Type-safety

- Don’t use implicit / explicit `any` or @ts-ignore

### Use auto generated types for new features

- For new features and endpoints that are covered by OpenApi schemas, we should use auto generated types and
typed http client

### Naming conventions on most used variables such as handlers, booleans etc

- Use descriptive naming (such as the use of is) that follows natural convention such as `isFormVerified`
or `isAuthenticated` instead of *verified*, *authenticated* etc
- Use descriptive naming for event handlers such as `onIconClick` or `onInputChange` rather than *handleChange*
- Include the **verb** part in the functions’ names
- For **3 or more** function arguments use object destructuring
<https://github.com/ryanmcdermott/clean-code-javascript?tab=readme-ov-file#function-arguments-2-or-fewer-ideally>
- For functions that return other functions getBlaBlaHandler (in case of handlers) or getBlaBlaFn
(if it’s not handler that is returned)
- Don’t use higher-ordered functions without clear need

## State management

### Don’t use returned values from MobX actions

- MobX actions should not return value that is later used within components. Instead MobX actions should update
observables and then components should consume observables to reflect data updates.

### Leverage small global stores over local state passed as props over multiple levels

- Create small specialized store in MobX even for small feature
instead of relying on local state that is passed down the React tree over multiple levels
e.g.:
  alert_receive_channel_connected_channels.ts
  alert_receive_channel_webhooks.ts

### Use global decorators / custom hooks / utilities consistently

- For example:
  - `@WithGlobalNotification` to set successful / failing notification based on MobX action’s result
  - `@AutoLoadingState` to manage loading statuses of async actions
  - `useIsLoading` to consume loading state
  - `useDrawer` to manage drawers
  - `useConfirmModal` to manage confirm modal
  - Global helpers

## Code organization

### Store files in appropriate places

- Store files in appropriate places (components, containers, models etc)
- Helpers and configs should be stored in the same folder with the appropriate name
e.g. [container].helper.ts, [container].config.ts
- Project-wide utilities should be placed in the **utils** folder`
- Use named exports for all code you want to export from a file.
- Export only the code that is meant to be used outside the module.

### Don’t opt-out from eslint / TS rules

- Avoid opting out from eslint or TS rules unless there is a strong reason / lack of possibility to follow the rule

## Styling

### Use Emotion.js with agreed code style

- Use emotion.js for styling
- Make use of `useStyles2` hook
- Use css `` syntax
- Place `getStyles` function at the end of the same file or in the separate file with `X.styles.ts` suffix
(if it’s reused by multiple components or it’s too large for placing in the same component’s file)

## React

### Keep components functional and small

- Use functional components for new features
- Leverage components composition, use many small components, render list items in dedicated component
and dereference values late
<https://mobx.js.org/react-optimizations.html>
- Keep components small and flat
- Use dedicated components over render functions in case a there's a risk that a single component grows too much
- Static values (especially non-primitive) that don’t depend on local state, props or store should be extracted
out of component
- Don’t create unnecessary local state that duplicates parts of global store
- Leverage custom hooks to extract repetitive logic
- Don’t use useMemo / useCallback by default

## Architecture

### Use layered architecture

- Don’t interact with backend directly from components
- Don’t interact with 3rd party (faro, web storage etc) directly but rather through service

## Frontend-backend communication

### Use typed HTTP request and response payloads

- HTTP request payload and response payload should always be typed
- Use typed http client whenever we have auto-generated types available
