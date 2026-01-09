const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// 1. ROBUST ENV LOADING
const envPath = path.resolve(__dirname, '../.env.local');
const envConfig = dotenv.config({ path: envPath });

console.log(`🔍 Looking for config at: ${envPath}`);

if (envConfig.error) {
  console.error("❌ Error loading .env.local file:", envConfig.error.message);
  process.exit(1);
}

const supabaseUrl = process.env.VITE_SUPABASE_URL || envConfig.parsed?.VITE_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || 
                    process.env.VITE_SUPABASE_ANON_KEY || 
                    envConfig.parsed?.SUPABASE_SERVICE_ROLE_KEY || 
                    envConfig.parsed?.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error("❌ CRITICAL ERROR: Missing API Credentials.");
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// --- HELPER: Strip HTML Tags ---
function stripHtml(str) {
  if (!str) return "";
  return str.toString().replace(/<[^>]*>?/gm, '').trim();
}

async function ingestData() {
  console.log("⚡ ASTA DATA REFINERY: Starting Ingestion...");

  let rawData = [];
  try {
    const dataPath = path.resolve(__dirname, '../scraped_listings.json');
    const fileContent = fs.readFileSync(dataPath, 'utf8');
    rawData = JSON.parse(fileContent);
    console.log(`📦 Loaded ${rawData.length} raw records.`);
  } catch (e) {
    console.error("❌ Error: Could not read 'scraped_listings.json'.");
    return;
  }

  const cleanData = rawData.map(item => {
    // Robust Price Parsing
    const rawPrice = item.price ? item.price.toString().replace(/[^0-9.]/g, '') : '0';
    const price = parseFloat(rawPrice) || 0;

    // Type Detection
    const type = (item.type?.toLowerCase().includes('rent') || 
                  item.title?.toLowerCase().includes('rent')) ? 'rent' : 'sale';

    return {
      title: stripHtml(item.title) || "Unverified Asset",
      description: stripHtml(item.description) || "Imported via Scout Scraper",
      price: price,
      currency: item.currency || 'GHS',
      type: type,
      status: 'active',
      
      // Geo-Jitter
      lat: (parseFloat(item.latitude) || 5.6037) + (Math.random() * 0.01 - 0.005), 
      long: (parseFloat(item.longitude) || -0.1870) + (Math.random() * 0.01 - 0.005),
      
      location_name: item.location || "Greater Accra",
      location_address: item.address || item.location,
      location_accuracy: 'low',
      
      vibe_features: JSON.stringify(item.features || []),
      
      details: {
        bedrooms: parseInt(item.bedrooms || item.beds || 0),
        bathrooms: parseInt(item.bathrooms || item.baths || 0),
        area_sqm: parseInt(item.area || item.sqm || 0),
        amenities: item.features || []
      },
      
      source: 'scraper_import',
      metadata: { original_url: item.url, import_batch: new Date().toISOString() }
    };
  });

  console.log(`🚀 Injecting ${cleanData.length} assets...`);
  
  const { data, error } = await supabase
    .from('properties')
    .insert(cleanData)
    .select();

  if (error) {
    console.error("🔥 Injection Failed:", error.message);
  } else {
    console.log(`✅ SUCCESS: ${data.length} assets are live on the grid.`);
  }
}

ingestData();
