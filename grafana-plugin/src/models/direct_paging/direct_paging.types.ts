export type ManualAlertGroupPayload = {
  team: string | null;
  users: Array<{ id: string; important: boolean }>;
};
