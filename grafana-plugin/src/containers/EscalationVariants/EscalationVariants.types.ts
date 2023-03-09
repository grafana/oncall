export enum EscalationVariantsTab {
  Schedules,
  Escalations,
  Users,
}

export interface UserAvailability {
  warnings: Array<{ error: string; data: any }>;
}

export enum ResponderType {
  User,
  Schedule,
  // EscalationChain, // for future
}
