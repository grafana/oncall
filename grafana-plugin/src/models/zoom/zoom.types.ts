export interface ZoomChannel {
  id: string;
  channel_id: string;
  channel_name: string;
  is_default_channel: boolean;
}

export interface ZoomUserIdentity {
  zoom_user_id: string;
  email: string;
  display_name: string;
}
