export interface GrafanaTeam {
  id: string;
  name: string;
  email: string;
  avatar_url: string;
  is_sharing_resources_to_all: boolean;
  number_of_users_currently_oncall?: number;
}
