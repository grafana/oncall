type Responder = { id: string; important: boolean };

export type ManualAlertGroupPayload = {
  team: Responder | null;
  users: Responder[];
};
