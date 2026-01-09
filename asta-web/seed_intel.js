import { createClient } from '@supabase/supabase-js';

// --- CONFIGURATION ---
const SUPABASE_URL = 'https://tjwwymongjrdsgoxfbtn.supabase.co'; 
const SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRqd3d5bW9uZ2pyZHNnb3hmYnRuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTE5Mjg4OSwiZXhwIjoyMDY2NzY4ODg5fQ.UjTtbZj3wUJ10gdttQUhd6UGMxOtQ_oKo2g9drU3ngI';

const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

// GPS SECTORS - PAN-GHANA COVERAGE
const SECTORS = [
  // Greater Accra
  { name: 'East Legon', lat: 5.636, lng: -0.166, range: 0.015, city: 'Accra' },
  { name: 'Cantonments', lat: 5.583, lng: -0.166, range: 0.01, city: 'Accra' },
  { name: 'Airport Residential', lat: 5.605, lng: -0.173, range: 0.01, city: 'Accra' },
  { name: 'Osu', lat: 5.556, lng: -0.184, range: 0.01, city: 'Accra' },
  { name: 'Spintex', lat: 5.630, lng: -0.120, range: 0.03, city: 'Accra' },
  // Ashanti
  { name: 'Ahodwo', lat: 6.667, lng: -1.616, range: 0.015, city: 'Kumasi' },
  { name: 'Knust Area', lat: 6.674, lng: -1.571, range: 0.02, city: 'Kumasi' },
  // Western
  { name: 'Takoradi Harbor', lat: 4.891, lng: -1.752, range: 0.02, city: 'Takoradi' },
  // Central
  { name: 'Cape Coast Castle Area', lat: 5.105, lng: -1.246, range: 0.01, city: 'Cape Coast' },
  // Northern
  { name: 'Tamale Central', lat: 9.404, lng: -0.839, range: 0.04, city: 'Tamale' },
  { name: 'Wa Municipality', lat: 10.060, lng: -2.501, range: 0.03, city: 'Wa' },
  // Eastern / Volta
  { name: 'Aburi Mountains', lat: 5.845, lng: -0.176, range: 0.02, city: 'Aburi' },
  { name: 'Ho Township', lat: 6.611, lng: 0.471, range: 0.03, city: 'Ho' },
  // Brong Ahafo
  { name: 'Sunyani Central', lat: 7.334, lng: -2.312, range: 0.03, city: 'Sunyani' }
];

const VIBES = ['Pool', 'Security', 'Modern', 'Luxury', 'Solar', 'Borehole', 'Smart Home', 'Gated Community', 'Ocean View', 'Generator'];
const IMAGES = [
  'https://images.unsplash.com/photo-1613490493576-7fde63acd811',
  'https://images.unsplash.com/photo-1512917774080-9991f1c4c750',
  'https://images.unsplash.com/photo-1600585154340-be6161a56a0c',
  'https://images.unsplash.com/photo-1480074568708-e7b720bb3f09',
  'https://images.unsplash.com/photo-1580587767503-3997489cdad5'
];

async function seedIntelligence() {
  console.log("🛰️ INITIALIZING PAN-GHANA SEED PROTOCOL...");
  
  const listings = [];
  // Generating 50 Listings
  for (let i = 0; i < 50; i++) {
    const sector = SECTORS[Math.floor(Math.random() * SECTORS.length)];
    const type = Math.random() > 0.4 ? 'sale' : 'rent';
    
    // Jitter coordinates to avoid stacking
    const lat = sector.lat + (Math.random() - 0.5) * sector.range;
    const lng = sector.lng + (Math.random() - 0.5) * sector.range;

    const price = type === 'sale' 
      ? Math.floor(Math.random() * 6000000) + 450000 // 450k - 6.45M GHS
      : Math.floor(Math.random() * 35000) + 2500;    // 2.5k - 37.5k GHS

    const selectedVibes = VIBES.sort(() => 0.5 - Math.random()).slice(0, 4);
    const mainImage = `${IMAGES[Math.floor(Math.random() * IMAGES.length)]}?auto=format&fit=crop&w=1200&q=80`;

    listings.push({
      owner_id: 'a6c318f7-e5fb-4b7a-90a1-5b1d9afc577a',
      title: `${sector.name} Residency ${i + 1}`,
      description: `Premium tactical asset located in the heart of ${sector.city}. Features include ${selectedVibes.join(', ')}. Verified by Asta Field Agents.`,
      price: price,
      currency: 'GHS',
      status: 'active',
      type: type,
      location_name: `${sector.name}, ${sector.city}`,
      location_address: `${sector.name}, ${sector.city}, Ghana`,
      lat: lat,
      long: lng, // Matched to 'long' in schema
      location_accuracy: 'high',
      vibe_features: selectedVibes.join(', '), // Stored as Text in schema
      cover_image_url: mainImage, // Matched to 'cover_image_url' in schema
      source: 'seed_script',
      details: { bedrooms: Math.floor(Math.random() * 5) + 1, bathrooms: Math.floor(Math.random() * 4) + 1 }
    });
  }

  console.log("📦 DEPLOYING ASSETS...");
  const { data, error } = await supabase.from('properties').insert(listings).select();

  if (error) {
    console.error("❌ DEPLOYMENT FAILURE:", error.message);
  } else {
    console.log(`✅ SUCCESS: ${data.length} ASSETS DEPLOYED.`);
    
    // Create Gallery Images for each property
    const galleryItems = [];
    data.forEach(prop => {
      // Add the cover image as a hero in the images table
      galleryItems.push({
        property_id: prop.id,
        url: prop.cover_image_url,
        is_hero: true
      });
      // Add one extra random image
      galleryItems.push({
        property_id: prop.id,
        url: `${IMAGES[Math.floor(Math.random() * IMAGES.length)]}?auto=format&fit=crop&w=800&q=80`,
        is_hero: false
      });
    });

    const { error: imgError } = await supabase.from('property_images').insert(galleryItems);
    
    if (imgError) {
      console.warn("⚠️ GALLERY WARNING:", imgError.message);
    } else {
      console.log("📸 GALLERY DATA SYNCED.");
    }
  }
}

seedIntelligence();
