import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface LicenseForm {
  id: string;
  email: string;
  wallet_address: string;
  payment_hash: string;
  language: string;
  license_key: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}
