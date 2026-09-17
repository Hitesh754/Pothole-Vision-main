import { createClient } from '@supabase/supabase-js';

// Read from environment variables if provided, with demo keys as fallback
const supabaseUrl = (import.meta as any).env?.VITE_SUPABASE_URL || 'https://bnuanukcnsghfrnsxlmb.supabase.co';
const supabaseKey = (import.meta as any).env?.VITE_SUPABASE_PUBLISHABLE_KEY || (import.meta as any).env?.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJudWFudWtjbnNnaGZybnN4bG1iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3NDQ2MjksImV4cCI6MjA4NTMyMDYyOX0.n8KZUbJNbii8vtog2q1mjBxoCrQT8drgqv3L2GpojZg';

export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
    detectSessionInUrl: false
  }
});