import { supabase } from './supabase';

// Define loose types locally to avoid dependency errors
type Property = any; 
type Profile = any;

interface TrustScore {
  score: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  label: string;
  color: string;
  breakdown: {
    agentTrust: number;
    locationFidelity: number;
    socialProof: number;
    visualProof: number;
  };
}

export function calculateTrustScore(property: Property, owner?: Profile): TrustScore {
  let score = 0;
  const breakdown = {
    agentTrust: 0,
    locationFidelity: 0,
    socialProof: 0,
    visualProof: 0,
  };

  // 1. AGENT CREDIBILITY (Max 40 pts)
  // We check the verification_tier of the owner
  if (owner) {
    if (owner.verification_tier === 'pro_agent') {
      breakdown.agentTrust = 40;
    } else if (owner.verification_tier === 'verified_scout') {
      breakdown.agentTrust = 30;
    } else {
      breakdown.agentTrust = 10; // Basic user
    }
  }
  score += breakdown.agentTrust;

  // 2. LOCATION FIDELITY (Max 25 pts)
  // 'high' accuracy means GPS pinned on site
  if (property.location_accuracy === 'high') {
    breakdown.locationFidelity = 25;
  } else {
    breakdown.locationFidelity = 5;
  }
  score += breakdown.locationFidelity;

  // 3. SOCIAL PROOF (Max 20 pts)
  // Net positive votes from the Scout network
  const votesGood = property.votes_good || 0;
  const votesBad = (property.votes_bad || 0) + (property.votes_scam || 0);
  const netVotes = votesGood - votesBad;

  if (netVotes >= 10) {
    breakdown.socialProof = 20;
  } else if (netVotes >= 1) {
    breakdown.socialProof = 10;
  } else if (netVotes < 0) {
    breakdown.socialProof = 0; // Penalty zone handled in grade
  }
  score += breakdown.socialProof;

  // 4. VISUAL PROOF (Max 15 pts)
  if (property.cover_image_url && property.cover_image_url.length > 10) {
    breakdown.visualProof = 15;
  }
  score += breakdown.visualProof;

  // GRADING LOGIC
  let grade: TrustScore['grade'] = 'F';
  let label = 'High Risk';
  let color = 'text-red-500';

  if (score >= 90) {
    grade = 'A';
    label = 'Verified Asset';
    color = 'text-emerald-400';
  } else if (score >= 75) {
    grade = 'B';
    label = 'High Trust';
    color = 'text-blue-400';
  } else if (score >= 50) {
    grade = 'C';
    label = 'Standard';
    color = 'text-yellow-400';
  } else {
    grade = 'D'; // Or F
    label = 'Unverified';
    color = 'text-orange-500';
  }

  // Override for Scam Flags
  if (votesBad > 5 && votesBad > votesGood) {
    grade = 'F';
    label = 'Community Flagged';
    color = 'text-red-600';
    score = 0;
  }

  return { score, grade, label, color, breakdown };
}

// --- SECURE INBOX WIRING ---

export async function sendSecureMessage(
  recipientId: string, 
  content: string, 
  senderId?: string | null
) {
  try {
    // If no senderId is provided (anonymous user), we set it to null
    // and flag it as a system alert so the UI treats it differently.
    const { data, error } = await supabase
      .from('messages')
      .insert([
        {
          recipient_id: recipientId,
          sender_id: senderId || null, 
          content: content,
          is_system_alert: !senderId, // True if anonymous
          created_at: new Date().toISOString(),
        }
      ])
      .select();

    if (error) throw error;
    return { success: true, data };
  } catch (error) {
    console.error("Secure Transmission Failed:", error);
    return { success: false, error };
  }
}
