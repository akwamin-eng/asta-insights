export const GHANA_REGIONS = [
  "Greater Accra",
  "Ashanti",
  "Western",
  "Central",
  "Eastern",
  "Northern",
  "Volta",
  "Bono",
  "Upper East",
  "Upper West",
] as const;

export type RegionName = (typeof GHANA_REGIONS)[number];

// 🧠 THE BRAIN: Maps specific cities/towns to their Region
const CITY_REGION_MAP: Record<string, RegionName> = {
  // GREATER ACCRA
  Accra: "Greater Accra",
  Tema: "Greater Accra",
  Legon: "Greater Accra",
  "East Legon": "Greater Accra",
  Spintex: "Greater Accra",
  Cantonments: "Greater Accra",
  Osu: "Greater Accra",
  "Airport City": "Greater Accra",
  "Tse Addo": "Greater Accra",
  "New Ningo": "Greater Accra",
  Sakumono: "Greater Accra",
  Lashibi: "Greater Accra",
  Adenta: "Greater Accra",
  Madina: "Greater Accra",
  Dzorwulu: "Greater Accra",
  Achimota: "Greater Accra",
  Kasoa: "Greater Accra", // Often mapped here for market relevance
  Prampram: "Greater Accra",
  Dodowa: "Greater Accra",
  Ada: "Greater Accra",

  // ASHANTI
  Kumasi: "Ashanti",
  Obuasi: "Ashanti",
  Ejisu: "Ashanti",
  Mampong: "Ashanti",
  Konongo: "Ashanti",
  Ahodwo: "Ashanti",
  Nhyiaeso: "Ashanti",
  Knust: "Ashanti",

  // WESTERN
  Takoradi: "Western",
  Sekondi: "Western",
  Tarkwa: "Western",
  Axim: "Western",
  Elubo: "Western",
  Bogoso: "Western",
  Prestea: "Western",

  // CENTRAL
  "Cape Coast": "Central",
  Cape: "Central", // Common abbreviation
  Winneba: "Central",
  Elmina: "Central",
  Swedru: "Central",
  "Kasoa (Central)": "Central",
  Mankessim: "Central",

  // NORTHERN
  Tamale: "Northern",
  Yendi: "Northern",
  Savelugu: "Northern",
  Walewale: "Northern",
  Bimbilla: "Northern",
  Salaga: "Northern",

  // VOLTA
  Ho: "Volta",
  Hohoe: "Volta",
  Aflao: "Volta",
  Keta: "Volta",
  Sogakope: "Volta",
  Akatsi: "Volta",
  Kpando: "Volta",

  // EASTERN
  Koforidua: "Eastern",
  Aburi: "Eastern",
  Akosombo: "Eastern",
  Nsawam: "Eastern",
  Nkawkaw: "Eastern",
  Suhum: "Eastern",
  "Akim Oda": "Eastern",

  // BONO (Sunyani)
  Sunyani: "Bono",
  Techiman: "Bono",
  Berekum: "Bono",
  Dormaa: "Bono",
  Wenchi: "Bono",
  Kintampo: "Bono",

  // UPPER EAST
  Bolgatanga: "Upper East",
  Navrongo: "Upper East",
  Bawku: "Upper East",
  Paga: "Upper East",

  // UPPER WEST
  Wa: "Upper West",
  Tumu: "Upper West",
  Lawra: "Upper West",
};

/**
 * INTELLIGENCE RESOLVER
 * Takes a raw location string (e.g. "C5V4+FF5, Bolgatanga Rd, Tamale, Ghana")
 * and scans it for known keywords to find the Region.
 */
export function getRegionForLocation(location: string): RegionName {
  if (!location) return "Greater Accra";

  // 1. Exact Match (Fastest)
  if (CITY_REGION_MAP[location]) {
    return CITY_REGION_MAP[location];
  }

  // 2. Fuzzy Keyword Search (The "God Mode" Logic)
  const locationLower = location.toLowerCase();

  // Sort keys by length so we match "Cape Coast" before "Cape"
  const knownCities = Object.keys(CITY_REGION_MAP).sort(
    (a, b) => b.length - a.length
  );

  for (const city of knownCities) {
    if (locationLower.includes(city.toLowerCase())) {
      return CITY_REGION_MAP[city];
    }
  }

  // 3. Emergency Fallbacks (Common variations)
  if (locationLower.includes("accra") || locationLower.includes("tema"))
    return "Greater Accra";
  if (locationLower.includes("ks") || locationLower.includes("kumasi"))
    return "Ashanti";
  if (locationLower.includes("tdi") || locationLower.includes("takoradi"))
    return "Western";
  if (locationLower.includes("ucc") || locationLower.includes("cape"))
    return "Central";
  if (locationLower.includes("tamale") || locationLower.includes("northern"))
    return "Northern";
  if (locationLower.includes("volta") || locationLower.includes("ho"))
    return "Volta";

  // Default
  return "Greater Accra";
}
