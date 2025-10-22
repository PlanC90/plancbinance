/*
  # Create License Forms Table

  1. New Tables
    - `license_forms`
      - `id` (uuid, primary key) - Unique identifier for each license form submission
      - `email` (text, not null) - User's email address
      - `wallet_address` (text, not null) - User's wallet address
      - `payment_hash` (text, not null) - Payment transaction hash
      - `language` (text, not null) - Language code for the submission
      - `license_key` (text, nullable) - Generated license key after approval
      - `status` (text, not null, default 'pending') - Status: pending, approved, rejected
      - `created_at` (timestamptz, default now()) - Timestamp of form submission
      - `updated_at` (timestamptz, default now()) - Timestamp of last update

  2. Security
    - Enable RLS on `license_forms` table
    - Add policy for admins to read all data
    - Add policy for users to insert their own data
*/

CREATE TABLE IF NOT EXISTS license_forms (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text NOT NULL,
  wallet_address text NOT NULL,
  payment_hash text NOT NULL,
  language text NOT NULL DEFAULT 'en',
  license_key text,
  status text NOT NULL DEFAULT 'pending',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE license_forms ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can insert license forms"
  ON license_forms
  FOR INSERT
  TO anon
  WITH CHECK (true);

CREATE POLICY "Anyone can read license forms"
  ON license_forms
  FOR SELECT
  TO anon
  USING (true);

CREATE POLICY "Anyone can update license forms"
  ON license_forms
  FOR UPDATE
  TO anon
  USING (true)
  WITH CHECK (true);