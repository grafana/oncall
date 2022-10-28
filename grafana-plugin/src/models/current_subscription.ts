export interface CurrentSubscriptionDTO {
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
  users_limit: string;
  current_stats: {
    // users_on_call: User['pk'][];
    // users_1_weeks_ago: User['pk'][];
    // users_2_weeks_ago: User['pk'][];
    // users_3_weeks_ago: User['pk'][];
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
