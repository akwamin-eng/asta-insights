import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import type { UserProfile } from '../types/asta_types';

export interface IntelMessage {
  id: string;
  sender: string;
  subject: string;
  preview: string;
  body: string;
  timestamp: string;
  priority: 'high' | 'medium' | 'low';
  status: 'unread' | 'read';
  type: 'intel' | 'system' | 'alert';
  property_id?: string;
}

export function useHunterIntel(profile: UserProfile | null) {
  const [messages, setMessages] = useState<IntelMessage[]>([]);
  const [loading, setLoading] = useState(true);

  // FETCH LOGIC
  useEffect(() => {
    if (!profile) return;

    const fetchIntel = async () => {
      setLoading(true);
      
      const { data: dbMessages, error } = await supabase
        .from('messages')
        .select('*')
        .eq('recipient_id', profile.id)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('Error fetching intel:', error);
      }

      const realMessages: IntelMessage[] = (dbMessages || []).map((msg: any) => {
        const msgType = msg.is_system_alert ? 'alert' : 'intel';
        // Explicitly check for non-null read_at
        const status = msg.read_at ? 'read' : 'unread';
        
        const lines = msg.content.split('\n');
        const subject = lines[0].replace(/\*\*/g, '').replace('HUNTER ALERT:', '').trim() || 'Incoming Transmission';
        const preview = lines[1] || lines[0];

        return {
          id: msg.id,
          sender: msg.sender_id ? 'Field Agent' : 'ASTA SYSTEM',
          subject: subject,
          preview: preview.substring(0, 50) + '...',
          body: msg.content,
          timestamp: new Date(msg.created_at).toLocaleDateString(),
          priority: msg.is_system_alert ? 'high' : 'medium',
          status: status,
          type: msgType,
          property_id: msg.property_id ? msg.property_id.toString() : undefined
        };
      });

      const systemMsg: IntelMessage = {
        id: 'sys-welcome',
        sender: 'Central Command',
        subject: 'Identity Verified',
        preview: 'Access granted to Level 2 telemetry...',
        body: `AGENT: ${profile.full_name || 'Unknown'}\nRANK: ${profile.rank_title}\n\nYour neural link to the Asta Network is stable.\n\nReputation Score: ${profile.reputation_score || 0}\n\nUse the "Hunter Config" module to calibrate your target zones.`,
        timestamp: 'Now',
        priority: 'low',
        status: 'read', 
        type: 'system'
      };

      setMessages([systemMsg, ...realMessages]);
      setLoading(false);
    };

    fetchIntel();
    
    const subscription = supabase
      .channel('public:messages')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'messages', filter: `recipient_id=eq.${profile.id}` }, (payload) => {
         // Listen for ALL events (including UPDATE) to keep read status in sync
         fetchIntel();
      })
      .subscribe();

    return () => {
      supabase.removeChannel(subscription);
    };

  }, [profile]);

  // NEW ACTION: Mark message as read (PERSISTENT)
  const markAsRead = async (id: string) => {
    // 1. Optimistic Update
    setMessages(prev => prev.map(msg => 
      msg.id === id ? { ...msg, status: 'read' } : msg
    ));

    if (id.startsWith('sys-')) return;

    // 2. Database Update
    // We select the ID returned to ensure a row was actually touched
    const { data, error } = await supabase
      .from('messages')
      .update({ read_at: new Date().toISOString() })
      .eq('id', id)
      .select();

    if (error) {
      console.error('CRITICAL: Failed to update DB:', error);
    } else if (data.length === 0) {
      console.error('CRITICAL: RLS Policy blocked the update. Row not modified.');
    } else {
      console.log('Message successfully marked read in DB.');
    }
  };

  return { messages, loading, markAsRead };
}
