import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://tjwwymongjrdsgoxfbtn.supabase.co'; 
const SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRqd3d5bW9uZ2pyZHNnb3hmYnRuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTE5Mjg4OSwiZXhwIjoyMDY2NzY4ODg5fQ.UjTtbZj3wUJ10gdttQUhd6UGMxOtQ_oKo2g9drU3ngI';

const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

async function wipeSeededData() {
  console.log("🧹 INITIALIZING DATABASE SANITIZATION...");
  
  // This deletes properties where source is 'seed_script'
  const { error } = await supabase
    .from('properties')
    .delete()
    .eq('source', 'seed_script');

  if (error) {
    console.error("❌ WIPE FAILURE:", error.message);
  } else {
    console.log("✅ GRID SANITIZED: All test assets removed.");
  }
}

wipeSeededData();
