import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const POSTIZ_API_KEY = Deno.env.get('POSTIZ_API_KEY');
const POSTIZ_URL = Deno.env.get('POSTIZ_URL'); 

serve(async (req) => {
  // 1. Parse the Incoming Webhook Data from Supabase
  const { record } = await req.json(); 

  // 2. Initialize Admin Client
  const supabaseAdmin = createClient(
    Deno.env.get('SUPABASE_URL') ?? '',
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
  );

  try {
    console.log(`Hype Man activating for property: ${record.title}`);

    // 3. AI Brain (Mock Logic - Replace with OpenAI API call if desired)
    // We synthesize the property data into platform-specific hooks
    const viralHooks = {
      twitter: `🚨 JUST LISTED: ${record.title} in ${record.location_name}. Asking ${record.currency} ${record.price.toLocaleString()}. This vibe is unmatched. DM for early access! #AccraRealEstate #Ghana`,
      instagram: `The standard has been raised. ✨ ${record.title} in ${record.location_name} is now live on the Asta Grid. Tap the link in bio for the full dossier.`,
      linkedin: `New Asset Alert: High-yield residential opportunity in ${record.location_name}. ${record.title} is now available for private viewing via Asta.`
    };

    // 4. Dispatch to Postiz API
    // We send a single request to Postiz to handle the cross-platform distribution
    const postizResponse = await fetch(`${POSTIZ_URL}/api/v1/posts`, {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${POSTIZ_API_KEY}`,
        'Content-Type': 'application/json' 
      },
      body: JSON.stringify({
        posts: [
          { platform: 'twitter', text: viralHooks.twitter, media: [record.cover_image_url] },
          { platform: 'instagram', text: viralHooks.instagram, media: [record.cover_image_url] }
        ],
        schedule: "now"
      })
    });

    if (!postizResponse.ok) throw new Error('Postiz Dispatch Failed');

    // 5. Update Marketing Logs (Proof of Work)
    // This allows the user to see "Queued/Posted" in their Dossier
    await supabaseAdmin.from('marketing_logs').insert([
      { property_id: record.id, platform: 'twitter', caption_used: viralHooks.twitter, status: 'posted' },
      { property_id: record.id, platform: 'instagram', caption_used: viralHooks.instagram, status: 'posted' }
    ]);

    return new Response(JSON.stringify({ message: "Amplify sequence complete" }), { 
      headers: { "Content-Type": "application/json" },
      status: 200 
    });

  } catch (error) {
    console.error(`Amplify Error: ${error.message}`);
    
    // Log the failure so the user knows why it didn't post
    await supabaseAdmin.from('marketing_logs').insert({ 
      property_id: record.id, 
      platform: 'system', 
      status: 'failed',
      caption_used: error.message
    });

    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
})
