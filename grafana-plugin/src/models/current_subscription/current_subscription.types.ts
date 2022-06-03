interface UpdateLicenseOption {
  per_month: {
    price: number;
    product_id: number;
  };
  per_year: {
    price: number;
    product_id: number;
  };
}

export interface Subscription {
  uuid: string;
  created_at: string;
  activation_expire_at: any;
  charges: string;
  stats: {
    result_credit: string;
    result_active_users_number: string;
    month: string;
  };
  subscription_plan: string;

  active_plan: string;
  expires_at: string;

  active_users: string[];
  stakeholders: string[];
  active_users_count: number;
  users_limit: number;
  stakeholders_count: number;
  stakeholders_limit: number;

  show_stakeholders_in_violation_message: boolean;

  update_licence_options: {
    business: UpdateLicenseOption;
    team: UpdateLicenseOption;
  };

  current_team_primary_key: number;
  current_user_primary_key: number;

  trial_days_left: number;

  current_stats: {
    users_on_call: any[];
    users_1_weeks_ago: any[];
    users_2_weeks_ago: any[];
    users_3_weeks_ago: any[];
    active_users_count: number;
    estimate_credit: number;

    is_billing_exists: boolean;
    active_plan: string;
    expires_at: string;
    paid_up_users: number;
    active_users: number;
    admins: number;
    users: number;

    active_users_history: Array<{
      month: string;
      active_users_amount: number;
    }>;

    billing_history: Array<{
      date: string;
      plan: number;
      paid_up_users_amount: number;
      charges: string;
      active_users: number;
      billing_statement: string;
      planned_next_period: boolean;
    }>;

    usage_statistics: {
      users_on_call: string[];
      users_1_weeks_ago: string[];
      users_2_weeks_ago: string[];
      users_3_weeks_ago: string[];
      active_users_count: number;
      estimate_credit: number;
    };
  };
}
