const { createClient } = require('@supabase/supabase-js');
const dotenv = require('dotenv');
const path = require('path');

// 1. Load Environment Variables
const envPath = path.resolve(__dirname, '../.env.local');
const envConfig = dotenv.config({ path: envPath });

const supabaseUrl = process.env.VITE_SUPABASE_URL || envConfig.parsed?.VITE_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || 
                    process.env.VITE_SUPABASE_ANON_KEY || 
                    envConfig.parsed?.SUPABASE_SERVICE_ROLE_KEY || 
                    envConfig.parsed?.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error("❌ Error: Missing API Credentials in .env.local");
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// --- HELPER: Strip HTML Tags ---
function stripHtml(str) {
  if (!str) return "";
  return str.toString().replace(/<[^>]*>?/gm, '').trim();
}

async function migrateData() {
  console.log("⚡ ASTA MIGRATION PROTOCOL: Market Listings -> Live Properties");

  console.log("... Fetching raw intelligence from 'market_listings' table...");
  const { data: rawListings, error: fetchError } = await supabase
    .from('market_listings')
    .select('*');

  if (fetchError) {
    console.error("❌ Error fetching source data:", fetchError.message);
    return;
  }

  if (!rawListings || rawListings.length === 0) {
    console.log("⚠️  No data found in 'market_listings'.");
    return;
  }

  console.log(`📦 Found ${rawListings.length} raw records.`);

  const cleanData = rawListings.map(row => {
    const item = row.raw_data || row; 

    // Robust Price Parsing
    const rawPrice = (item.price || row.price || '0').toString().replace(/[^0-9.]/g, '');
    const price = parseFloat(rawPrice) || 0;

    // Type Detection
    const titleRaw = item.title || row.title || "Unverified Asset";
    const type = (titleRaw.toLowerCase().includes('rent')) ? 'rent' : 'sale';

    // Parse Details for Calculators
    const details = {
      bedrooms: parseInt(item.bedrooms || item.beds || 0),
      bathrooms: parseInt(item.bathrooms || item.baths || 0),
      area_sqm: parseInt(item.area || item.sqm || 0),
      amenities: item.features || [],
      meta_original_id: row.id,
      meta_original_url: row.url
    };

    return {
      title: stripHtml(titleRaw),
      description: stripHtml(item.description) || "Migrated from Market Listings",
      price: price,
      currency: 'GHS',
      type: type,
      status: 'active',
      
      // Geolocation with Jitter
      lat: (row.geo_point?.lat || item.latitude || 5.6037) + (Math.random() * 0.02 - 0.01), 
      long: (row.geo_point?.long || item.longitude || -0.1870) + (Math.random() * 0.02 - 0.01),
      
      location_name: row.location || item.location || "Greater Accra",
      location_address: row.location || item.address,
      location_accuracy: 'low', 
      
      vibe_features: JSON.stringify(item.features || []),
      details: details,
      
      source: 'internal_migration'
    };
  });

  console.log(`🚀 Migrating ${cleanData.length} assets to the Live Grid...`);
  
  const { data, error } = await supabase
    .from('properties')
    .insert(cleanData)
    .select();

  if (error) {
    console.error("🔥 Migration Failed:", error.message);
  } else {
    console.log(`✅ SUCCESS: ${data.length} assets are now LIVE.`);
    console.log("   -> Dashboard & Maps should now populate.");
  }
}

migrateData();
