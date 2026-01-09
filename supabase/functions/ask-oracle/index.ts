import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const GEMINI_API_KEY = Deno.env.get("GEMINI_API_KEY");

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  // 1. Handle CORS
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // 2. Validate Key
    if (!GEMINI_API_KEY) {
      throw new Error("GEMINI_API_KEY is not set in Supabase Secrets.");
    }

    const { query, context } = await req.json();

    // 3. Construct Prompt
    const systemPrompt = `
      You are the "Asta Market Oracle", an expert real estate analyst.
      Analyze this JSON market data and answer the user question.
      
      Metrics Definitions:
      - "Heat Score" = Demand (Leads) / Supply (Listings).
      - > 2.0 = High Demand (Undersupplied).
      
      Data Context:
      ${JSON.stringify(context)}
    `;

    // 4. Call Gemini API - Primary Strategy (Using your active model)
    // ⚡ FIX: Updated to 'gemini-2.0-flash' based on your dashboard usage
    const primaryModel = "gemini-2.0-flash";
    const primaryUrl = `https://generativelanguage.googleapis.com/v1beta/models/${primaryModel}:generateContent?key=${GEMINI_API_KEY}`;

    let response = await fetch(primaryUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [
          { parts: [{ text: systemPrompt + "\n\nUser Question: " + query }] },
        ],
      }),
    });

    let data = await response.json();

    // 5. Fallback Strategy
    if (!response.ok) {
      console.warn(
        `Primary model (${primaryModel}) failed. Attempting fallback to gemini-1.5-flash...`
      );

      const fallbackModel = "gemini-1.5-flash";
      const fallbackUrl = `https://generativelanguage.googleapis.com/v1beta/models/${fallbackModel}:generateContent?key=${GEMINI_API_KEY}`;

      response = await fetch(fallbackUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [
            { parts: [{ text: systemPrompt + "\n\nUser Question: " + query }] },
          ],
        }),
      });

      data = await response.json();

      if (!response.ok) {
        console.error("Gemini Fallback Error:", JSON.stringify(data));
        throw new Error(
          `Gemini Error: ${data.error?.message || "All models failed."}`
        );
      }
    }

    const aiText = data.candidates?.[0]?.content?.parts?.[0]?.text;

    if (!aiText) {
      throw new Error("Gemini returned no candidates.");
    }

    return new Response(JSON.stringify({ answer: aiText }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Edge Function Error:", error.message);
    return new Response(JSON.stringify({ answer: `Error: ${error.message}` }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
