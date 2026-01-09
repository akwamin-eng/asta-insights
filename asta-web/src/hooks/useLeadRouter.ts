import { useState } from 'react';
import { supabase } from '../lib/supabase';

export function useLeadRouter() {
  const [loading, setLoading] = useState(false);

  const createLeadAndRedirect = async (
    property: any,
    inquirer: { name: string; phone: string; message: string },
    user?: any
  ) => {
    setLoading(true);
    const startTime = Date.now();

    try {
      // 1. Log the Lead (The Analytics Trace)
      const { error } = await supabase.from('leads').insert({
        property_id: property.id,
        user_id: user?.id || null,
        inquirer_name: inquirer.name,
        phone: inquirer.phone, 
        message_preview: inquirer.message,
        source: 'whatsapp_bridge',
        status: 'new'
      });

      if (error) console.error('Lead log failed:', error);

      // 2. Identify the Target Agent
      // Precedence: Property specific phone > Property Owner's phone > System Default
      const targetPhone = property.contact_phone || 
                         property.phone || 
                         property.owner?.phone_number || 
                         "233540000000"; 

      const cleanPhone = targetPhone.toString().replace(/[^0-9]/g, '');

      // 3. Construct High-Context Payload
      // We format this for maximum readability in the WhatsApp UI
      const messageBody = 
        `*ASTA LEAD TERMINAL*\n` +
        `--------------------------\n` +
        `*Property:* ${property.title}\n` +
        `*Price:* ${property.currency} ${property.price.toLocaleString()}\n` +
        `*Location:* ${property.location_name}\n\n` +
        `*Inquirer:* ${inquirer.name}\n` +
        `*Contact:* ${inquirer.phone}\n` +
        `*Notes:* ${inquirer.message}\n` +
        `--------------------------\n` +
        `_Generated via Asta Intelligence_`;

      const url = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(messageBody)}`;

      // 4. Tactical Delay for UX feedback
      const elapsed = Date.now() - startTime;
      if (elapsed < 800) {
        await new Promise(r => setTimeout(r, 800 - elapsed));
      }

      // 5. Open Secure Uplink
      window.open(url, '_blank');
      return { success: true };

    } catch (err) {
      console.error('Lead routing error:', err);
      return { success: false };
    } finally {
      setLoading(false);
    }
  };

  return { createLeadAndRedirect, loading };
}
