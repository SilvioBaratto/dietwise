export interface UserSettingsIn {
  age?: number;
  sex?: string;
  weight?: number;
  height?: number;
  other_data?: string;
  goals?: string;
}

export interface UserSettingsOut extends UserSettingsIn {
  readonly id: string;
  readonly user_id: string;
  readonly created_at: string;
  readonly updated_at: string;
}
