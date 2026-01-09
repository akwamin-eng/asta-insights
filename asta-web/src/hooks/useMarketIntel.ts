import { useState, useEffect } from "react";
import { supabase } from "../lib/supabase";

export interface IntelItem {
  id: string;
  title: string;
  summary?: string;
  sentiment: "positive" | "negative" | "neutral";
  source: string;
  date: string;
  type: "news" | "market_report" | "listing_signal";
  url?: string;
}

export function useMarketIntel() {
  const [intel, setIntel] = useState<IntelItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchIntel() {
      try {
        setLoading(true);

        // 1. Fetch News
        const { data: news } = await supabase
          .from("market_news")
          .select(
            "id, title, summary, ai_summary, sentiment_score, source, published_at, url"
          )
          .order("published_at", { ascending: false })
          .limit(5);

        // 2. Fetch Market Insights
        const { data: insights } = await supabase
          .from("ghana_market_insights")
          .select("id, title, confidence, insight_source, publish_time")
          .limit(1);

        // 3. Fetch Signals
        const { data: signals } = await supabase
          .from("market_listings")
          .select("id, title, price, location, source, last_seen_at")
          .order("last_seen_at", { ascending: false })
          .limit(2);

        // --- NORMALIZATION ---

        const formattedNews = (news || []).map((n) => ({
          id: n.id,
          title: n.title,
          summary: n.ai_summary || n.summary || "No summary available",
          sentiment:
            (n.sentiment_score || 0) > 0
              ? "positive"
              : (n.sentiment_score || 0) < 0
              ? "negative"
              : "neutral",
          source: n.source || "Asta Scout",
          date: n.published_at,
          type: "news" as const,
          url: n.url,
        }));

        const formattedInsights = (insights || []).map((i) => ({
          id: i.id,
          title: i.title,
          summary: `Confidence: ${i.confidence}% - Analyst Report`,
          sentiment: "neutral",
          source: i.insight_source || "Market Analyst",
          date: i.publish_time,
          type: "market_report" as const,
        }));

        const formattedSignals = (signals || []).map((s) => ({
          id: s.id,
          title: `New Signal: ${s.location}`,
          summary: `Market data point captured. Listing Price: ${s.price?.toLocaleString()}`,
          sentiment: "neutral",
          source: "Grid Scanner",
          date: s.last_seen_at || new Date().toISOString(),
          type: "listing_signal" as const,
        }));

        // 🟢 FIX: Merge, Sort, then SLICE to strictly 5 items
        const combined = [
          ...formattedSignals,
          ...formattedNews,
          ...formattedInsights,
        ]
          .sort(
            (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
          )
          .slice(0, 5); // <--- HARD CAP

        setIntel(combined);
      } catch (e) {
        console.error("Intel Fetch Error:", e);
      } finally {
        setLoading(false);
      }
    }

    fetchIntel();
  }, []);

  return { intel, loading };
}
