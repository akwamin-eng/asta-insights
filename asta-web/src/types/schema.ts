export type ListingStatus = "active" | "draft" | "sold" | "archived";
export type ListingType = "sale" | "rent";

export interface Property {
  id: number;
  owner_id: string;
  title: string;
  description?: string;
  price: number;
  currency: "GHS" | "USD";
  status: ListingStatus;
  type: ListingType;

  // Geospatial Data
  location_name: string;
  location_address?: string;
  lat?: number;
  long?: number;
  location_accuracy?: "high" | "low";

  // Metadata
  bedrooms?: number;
  image_urls?: string[];
  cover_image_url?: string;
  features?: string[];
  roi_score?: number;

  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  phone_number?: string;
  avatar_url?: string;
  role: "user" | "agent" | "admin";
  rank_title: "Observer" | "Scout" | "Elite" | "Legend";
  reputation_score: number;
  impact_stat: number;

  verification_tier: "basic" | "verified_scout" | "pro_agent";
  scout_segment:
    | "buyer"
    | "renter"
    | "investor_diaspora"
    | "investor_local"
    | "agent"
    | "developer";
  linkedin_url?: string;
  organization_name?: string;

  conversation_step?:
    | "IDLE"
    | "AWAITING_TYPE"
    | "AWAITING_LOCATION"
    | "AWAITING_PRICE"
    | "AWAITING_VIBE"
    | "AWAITING_CONFIRM";
  current_draft_id?: number;
}

export interface HunterPreferences {
  locations: string[];
  budget_max: number;
  property_type: string[];
  lifestyle_tags: string[];
  alerts_enabled: boolean;
  deal_trigger_percent: number;
}

export interface WatchlistItem {
  id: number;
  property_id: number;
  title: string;
  location: string;
  current_price: number;
  original_price: number;
  image_url: string;
  added_at: string;
}
