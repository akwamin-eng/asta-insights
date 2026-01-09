import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

console.log("Asta News Enricher (Gemini Protocol): Online");

Deno.serve(async (req) => {
  try {
    const { record } = await req.json();

    // Safety check
    if (!record.summary && !record.title) {
      return new Response("No content to analyze", { status: 200 });
    }

    console.log(`Analyzing news with Gemini: ${record.title}`);

    // 1. Prepare Gemini Request
    const apiKey = Deno.env.get("GEMINI_API_KEY");
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;

    const prompt = `
      You are a real estate analyst for the Ghanaian market. Analyze the following news snippet.
      Return a RAW JSON object (no markdown formatting) with these exact keys:
      {
        "sentiment_score": (number between -1.0 and 1.0),
        "ai_summary": (2 sentence executive summary),
        "relevance_score": (integer 1-10)
      }

      News Title: ${record.title}
      News Summary: ${record.summary}
    `;

    // 2. Call Gemini
    const aiResponse = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [
          {
            parts: [{ text: prompt }],
          },
        ],
        generationConfig: {
          response_mime_type: "application/json",
        },
      }),
    });

    const aiData = await aiResponse.json();

    // Error handling for Gemini
    if (!aiData.candidates || !aiData.candidates[0].content) {
      console.error("Gemini Error:", JSON.stringify(aiData));
      throw new Error("Invalid response from Gemini");
    }

    // 3. Parse Response
    const textResponse = aiData.candidates[0].content.parts[0].text;
    const content = JSON.parse(textResponse);

    // 4. Write Insights back to Supabase
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    await supabase
      .from("market_news")
      .update({
        sentiment_score: content.sentiment_score,
        ai_summary: content.ai_summary,
        relevance_score: content.relevance_score,
        status: "enriched",
      })
      .eq("id", record.id);

    return new Response(JSON.stringify(content), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error(error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
    });
  }
});
