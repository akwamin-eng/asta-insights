import { Shield, TrendingUp, Search, type LucideIcon } from 'lucide-react';

// --- 1. DEFINITIONS ---

export type BadgeTier = 'IRON' | 'BRONZE' | 'SILVER' | 'GOLD' | 'PLATINUM';

export interface RankDef {
  title: string;
  minScore: number;
  tier: BadgeTier;
  perk: string;
}

export interface ClassDef {
  id: string;
  label: string;
  description: string;
  icon: any; // LucideIcon type handled loosely for storage
  color: string;
}

// --- 2. RANK SYSTEM (The Ladder) ---

export const REPUTATION_RANKS: RankDef[] = [
  { title: 'Observer', minScore: 0, tier: 'IRON', perk: 'Read-only access to market signals.' },
  { title: 'Scout', minScore: 50, tier: 'BRONZE', perk: 'Can submit field reports for verification.' },
  { title: 'Operative', minScore: 200, tier: 'SILVER', perk: 'Access to "True Cost" advanced calculator.' },
  { title: 'Captain', minScore: 500, tier: 'GOLD', perk: 'Priority alerts & direct agent access.' },
  { title: 'Command', minScore: 1000, tier: 'PLATINUM', perk: 'Full platform visibility & API access.' }
];

// --- 3. CLASS SYSTEM (The Persona) ---

export const SCOUT_CLASSES: ClassDef[] = [
  { 
    id: 'buyer', 
    label: 'Asset Hunter', 
    description: 'I am actively looking for property to buy.',
    icon: Search,
    color: 'text-blue-400'
  },
  { 
    id: 'renter', 
    label: 'Urban Nomad', 
    description: 'I am looking for a rental in the city.',
    icon: Search,
    color: 'text-indigo-400'
  },
  { 
    id: 'investor_diaspora', 
    label: 'Global Tycoon', 
    description: 'I am investing from abroad (Diaspora).',
    icon: TrendingUp,
    color: 'text-emerald-400'
  },
  { 
    id: 'investor_local', 
    label: 'Local Mogul', 
    description: 'I am building a portfolio locally.',
    icon: TrendingUp,
    color: 'text-emerald-500'
  },
  { 
    id: 'agent', 
    label: 'Field Agent', 
    description: 'I represent properties or clients.',
    icon: Shield,
    color: 'text-orange-400'
  }
];

// --- 4. UTILITIES ---

export function getRankFromScore(score: number): RankDef {
  // Find the highest rank where score >= minScore
  // We reverse to find the highest match first
  return [...REPUTATION_RANKS].reverse().find(r => score >= r.minScore) || REPUTATION_RANKS[0];
}

export function getNextRank(currentScore: number): { next: RankDef | null, progress: number, needed: number } {
  const currentRank = getRankFromScore(currentScore);
  const currentIndex = REPUTATION_RANKS.findIndex(r => r.title === currentRank.title);
  const nextRank = REPUTATION_RANKS[currentIndex + 1];

  if (!nextRank) {
    return { next: null, progress: 100, needed: 0 };
  }

  const prevScore = currentRank.minScore;
  const targetScore = nextRank.minScore;
  
  // Calculate percentage progress between ranks
  // Example: Score 75 (Scout starts at 50, Operative at 200)
  // Progress = (75 - 50) / (200 - 50) = 25 / 150 = 16.6%
  const progress = Math.min(100, Math.max(0, ((currentScore - prevScore) / (targetScore - prevScore)) * 100));
  
  return {
    next: nextRank,
    progress,
    needed: targetScore - currentScore
  };
}
