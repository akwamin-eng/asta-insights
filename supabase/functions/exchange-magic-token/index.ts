import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  // Handle CORS (Browser requests)
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const supabaseAdmin = createClient(
    Deno.env.get("SUPABASE_URL") ?? "",
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
  );

  try {
    const { token } = await req.json();

    // 1. Verify the "Handshake Token" in our custom table
    const { data: linkRecord, error: linkError } = await supabaseAdmin
      .from("auth_magic_links")
      .select("*")
      .eq("token", token)
      .eq("used", false)
      .gt("expires_at", new Date().toISOString()) // Ensure not expired
      .single();

    if (linkError || !linkRecord) {
      return new Response(
        JSON.stringify({ error: "Invalid or expired token" }),
        {
          status: 401,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // 2. Mark as Used (One-time use)
    await supabaseAdmin
      .from("auth_magic_links")
      .update({ used: true })
      .eq("id", linkRecord.id);

    // 3. Get the User to check for Email
    const {
      data: { user },
    } = await supabaseAdmin.auth.admin.getUserById(linkRecord.user_id);

    if (!user) throw new Error("User not found");

    // 🛑 CRITICAL CHECK: Supabase requires an EMAIL to generate a Magic Link.
    // If the user only has a phone, we must assign a placeholder email temporarily.
    let targetEmail = user.email;

    if (!targetEmail) {
      const placeholderEmail = `${user.phone?.replace(
        "+",
        ""
      )}@placeholder.asta.homes`;
      // Update user with placeholder email so we can log them in
      await supabaseAdmin.auth.admin.updateUserById(user.id, {
        email: placeholderEmail,
        email_confirm: true,
      });
      targetEmail = placeholderEmail;
    }

    // 4. Generate Official Supabase Auth Link
    const { data: linkData, error: generateError } =
      await supabaseAdmin.auth.admin.generateLink({
        type: "magiclink",
        email: targetEmail,
      });

    if (generateError) throw generateError;

    // 5. Return the Action Link
    // The frontend will redirect to this, and Supabase will handle the rest (cookies, session, etc)
    return new Response(
      JSON.stringify({
        redirectUrl: linkData.properties.action_link,
      }),
      {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    console.error("Exchange Error:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
