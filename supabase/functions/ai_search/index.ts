// Asta Smart Search API (Powered by Gemini)
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { query } = await req.json()
    if (!query) throw new Error("No query provided")

    // 1. Get Embedding from Google Gemini (via REST API)
    // We use fetch because the node library isn't always Deno-friendly
    const googleKey = Deno.env.get('GOOGLE_API_KEY')
    const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key=${googleKey}`
    
    const geminiResp = await fetch(geminiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: "models/text-embedding-004",
        content: { parts: [{ text: query }] }
      })
    })

    const geminiData = await geminiResp.json()
    const embedding = geminiData.embedding.values

    // 2. Search Database
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    )

    const { data: listings, error } = await supabaseClient.rpc('search_listings', {
      query_embedding: embedding,
      match_threshold: 0.5, // 50% similarity minimum
      match_count: 10
    })

    if (error) throw error

    return new Response(JSON.stringify(listings), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 500,
    })
  }
})
