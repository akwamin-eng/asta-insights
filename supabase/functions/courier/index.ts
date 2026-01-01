import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const OPENAI_API_KEY = Deno.env.get('OPENAI_API_KEY');

serve(async (req) => {
  const supabaseAdmin = createClient(
    Deno.env.get('SUPABASE_URL') ?? '',
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
  );

  try {
    const formData = await req.formData();
    const body = formData.get('Body')?.toString().trim() || ''; 
    const from = formData.get('From')?.toString() || ''; 
    const numMedia = parseInt(formData.get('NumMedia')?.toString() || '0');
    const latitude = formData.get('Latitude');
    const longitude = formData.get('Longitude');
    
    // Clean Phone
    const phone = from.replace('whatsapp:', '');
    console.log(`📨 Msg: "${body}" | Media: ${numMedia} | From: ${phone}`);

    // 1. AUTH CHECK
    const { data: profile, error: profileError } = await supabaseAdmin
      .from('profiles')
      .select('*')
      .eq('phone_number', phone)
      .single();

    if (profileError || !profile) {
       console.error("Profile Error:", profileError);
       return twilioResponse("⛔ **Access Denied.**\n\nPlease register at **www.asta.homes** first.");
    }

    // --- RESET COMMAND ---
    if (body.toUpperCase() === 'RESET' || body.toUpperCase() === 'CANCEL') {
        await updateState(supabaseAdmin, profile.id, 'IDLE', null);
        return twilioResponse("🔄 **Session reset.**\n\nReady to list? Send your BEST photo to start listing safely.");
    }

    // --- STEP 0: WELCOME & LOGIN (Localhost Version) ---
    if (profile.conversation_step === 'IDLE' && numMedia === 0) {
        const magicToken = crypto.randomUUID();
        await supabaseAdmin.from('auth_magic_links').insert({ user_id: profile.id, token: magicToken });
        
        // 🚨 LOCALHOST LINK FOR TESTING 🚨
        const link = `http://localhost:5173/auth/magic?token=${magicToken}`;

        return twilioResponse(
            "👋 **Welcome to Asta, Scout.**\n\n" +
            "🔐 **Step 1: Authenticate Session**\n" +
            `Tap to verify identity:\n${link}\n\n` + 
            "_(After verifying, simply send a PHOTO to start listing)_"
        );
    }

    // --- STEP 1: PHOTO UPLOAD ---
    if (numMedia > 0) {
        console.log("📸 Processing Image...");
        
        // Create Draft
        const { data: draft, error: draftError } = await supabaseAdmin
            .from('properties')
            .insert({ owner_id: profile.id, status: 'draft', image_urls: [] })
            .select()
            .single();

        if (draftError) {
            console.error("Draft Creation Error:", draftError);
            return twilioResponse("⚠️ Database Error. Could not start draft.");
        }

        // Upload to Storage
        const mediaUrl = formData.get('MediaUrl0');
        if (mediaUrl) {
             console.log("⬇️ Downloading from Twilio...");
             const imageResp = await fetch(mediaUrl.toString());
             const imageBlob = await imageResp.blob();
             const filename = `${profile.id}/${draft.id}/cover.jpg`;
             
             console.log("⬆️ Uploading to Supabase...");
             const { error: uploadError } = await supabaseAdmin.storage
                .from('properties')
                .upload(filename, imageBlob, { contentType: 'image/jpeg', upsert: true });

             if (uploadError) {
                 console.error("Upload Error:", uploadError);
                 return twilioResponse("⚠️ Storage Error. Please make sure the 'properties' bucket exists and is public.");
             }

             const { data: { publicUrl } } = supabaseAdmin.storage.from('properties').getPublicUrl(filename);
             await supabaseAdmin.from('properties').update({ image_urls: [publicUrl] }).eq('id', draft.id);
        }

        await updateState(supabaseAdmin, profile.id, 'AWAITING_DESCRIPTION', draft.id);

        return twilioResponse(
            "✅ **Secure Upload.** Photo saved.\n\n" +
            "📝 **Tell me about this property.**\n" +
            "*(e.g. \"Modern 3 bedroom apartment in Osu for rent\")*"
        );
    }

    // --- STEP 2: AI DESCRIPTION ---
    if (profile.conversation_step === 'AWAITING_DESCRIPTION') {
        const step = profile.conversation_step;
        const draftId = profile.current_draft_id;

        const aiResponse = await analyzeWithAI(body);
        
        if (!aiResponse) {
             // Fallback if AI fails (or key is missing)
             return twilioResponse("🤖 **AI Error.**\n\nPlease check the server logs. In the meantime, describe the property again.");
        }

        await supabaseAdmin.from('properties').update({
            title: aiResponse.seo_title,
            description: aiResponse.seo_description,
            listing_type: aiResponse.intent,
            bedrooms: aiResponse.beds,
            features: aiResponse.features
        }).eq('id', draftId);

        await updateState(supabaseAdmin, profile.id, 'AWAITING_LOCATION', draftId);
        
        const intentEmoji = aiResponse.intent === 'sale' ? '🏷️' : '🔑';
        return twilioResponse(
            `✅ **Analysis Complete.**\n` +
            `${intentEmoji} Intent: **For ${aiResponse.intent?.toUpperCase()}**\n` +
            `🛏️ Beds: ${aiResponse.beds || 'Studio'}\n` +
            `📝 Title: "${aiResponse.seo_title}"\n\n` +
            "📍 **Location Verification**\n" +
            "📎 **Tap Attachment > Location**\n" +
            "👇 **Send the Pin**"
        );
    }
    
    // --- STEP 3: LOCATION ---
    if (profile.conversation_step === 'AWAITING_LOCATION') {
        const draftId = profile.current_draft_id;
        if (!latitude || !longitude) {
            return twilioResponse("🛑 **Use the Pin.**\n\nTyped addresses are not allowed. Please tap the Attachment icon and select Location.");
        }

        const lat = parseFloat(latitude.toString());
        const long = parseFloat(longitude.toString());

        // Ghana Fence
        const GHANA_BOUNDS = { minLat: 4.5, maxLat: 11.5, minLong: -3.5, maxLong: 1.5 };
        const isInsideGhana = lat >= GHANA_BOUNDS.minLat && lat <= GHANA_BOUNDS.maxLat && long >= GHANA_BOUNDS.minLong && long <= GHANA_BOUNDS.maxLong;

        if (!isInsideGhana) {
            await updateState(supabaseAdmin, profile.id, 'IDLE', null);
            return twilioResponse("🚫 **Out of Zone.**\n\nWe only support Ghana listings right now.");
        }

        await supabaseAdmin.from('properties').update({ 
            latitude: lat, longitude: long, location_name: "Geo-Pinned Location" 
        }).eq('id', draftId);
        
        await updateState(supabaseAdmin, profile.id, 'AWAITING_PRICE', draftId);

        return twilioResponse("🌍 **Coordinates Secured.**\n\n💰 **What is the price?** (e.g. 2000 USD)");
    }

    // --- STEP 4: PRICE ---
    if (profile.conversation_step === 'AWAITING_PRICE') {
        const draftId = profile.current_draft_id;
        const price = parseInt(body.replace(/[^0-9]/g, '')) || 0;
        let currency = 'GHS';
        if (body.toUpperCase().includes('USD') || body.includes('$')) currency = 'USD';

        await supabaseAdmin.from('properties').update({ price, currency }).eq('id', draftId);
        await updateState(supabaseAdmin, profile.id, 'AWAITING_VIBE', draftId);

        return twilioResponse(
            `💵 **Price Set:** ${price} ${currency}\n\n` +
            "🌟 **Sell the Vibe** (Reply with Number):\n[1] Quiet Luxury 🌿\n[2] Family Hub 👨‍👩‍👧\n[3] Generator-Ready 🔌\n[4] Commuter’s Dream 🚕"
        );
    }

    // --- STEP 5: PREVIEW ---
    if (profile.conversation_step === 'AWAITING_VIBE') {
        const draftId = profile.current_draft_id;
        let vibe = 'Standard';
        if (body === '1') vibe = 'Quiet Luxury';
        if (body === '2') vibe = 'Family Hub';
        if (body === '3') vibe = 'Generator-Ready';
        if (body === '4') vibe = 'Commuter Dream';

        const { data: draft } = await supabaseAdmin.from('properties').select('*').eq('id', draftId).single();
        const finalDesc = `${draft.description} (Vibe: ${vibe})`;
        await supabaseAdmin.from('properties').update({ description: finalDesc }).eq('id', draftId);
        await updateState(supabaseAdmin, profile.id, 'AWAITING_CONFIRM', draftId);

        return twilioResponse(
            "✨ **PREVIEW YOUR LISTING**\n\n" +
            `🏡 **${draft.title}**\n` +
            `💰 ${draft.currency} ${draft.price}\n` +
            `📝 ${draft.description.substring(0, 50)}...\n\n` +
            "✅ **Reply YES to publish instantly.**"
        );
    }

    // --- STEP 6: PUBLISH ---
    if (profile.conversation_step === 'AWAITING_CONFIRM') {
        if (body.toUpperCase().includes('YES')) {
            await supabaseAdmin.from('properties').update({ status: 'active' }).eq('id', profile.current_draft_id);
            await updateState(supabaseAdmin, profile.id, 'IDLE', null);
            return twilioResponse("🎉 **PUBLISHED!**\n\nYour listing is live.");
        }
        return twilioResponse("Type YES to publish.");
    }

    return twilioResponse("🤖 Send **RESET** to start over.");

  } catch (error) {
    console.error("Courier Crash:", error);
    return twilioResponse(`💔 System Error: ${error.message}`);
  }
})

async function analyzeWithAI(userText: string) {
    if (!OPENAI_API_KEY) { console.error("Missing AI Key"); return null; }
    try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${OPENAI_API_KEY}` },
            body: JSON.stringify({
                model: "gpt-4o-mini",
                messages: [
                    { role: "system", content: "You are a Real Estate SEO expert. Return JSON object (NO markdown) with fields: 'intent' ('sale' or 'rent'), 'beds' (number, null if unknown), 'features' (array of strings), 'seo_title' (catchy, max 50 chars), 'seo_description' (professional, max 150 chars)." },
                    { role: "user", content: userText }
                ]
            })
        });
        const data = await response.json();
        const content = data.choices[0].message.content;
        return JSON.parse(content.replace(/```json/g, '').replace(/```/g, ''));
    } catch (e) {
        console.error("AI Error:", e);
        return null;
    }
}

async function updateState(supabase: any, userId: string, step: string, draftId: any) {
    await supabase.from('profiles').update({ conversation_step: step, current_draft_id: draftId }).eq('id', userId);
}

function twilioResponse(message: string) {
  const xml = `<?xml version="1.0" encoding="UTF-8"?><Response><Message>${message}</Message></Response>`;
  return new Response(xml, { headers: { "Content-Type": "text/xml" }, status: 200 });
}
