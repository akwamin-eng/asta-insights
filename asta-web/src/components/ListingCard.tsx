import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { MapPin, ArrowRight } from "lucide-react";
import type { Property } from "../types/schema";

interface ListingCardProps {
  property: Property;
  onClick: () => void;
  isSelected?: boolean;
}

const getCleanTags = (raw: string | string[] | undefined) => {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw.slice(0, 3);
  return raw
    .replace(/[\[\]"']/g, "")
    .split(",")
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0)
    .slice(0, 3);
};

const STOCK_IMAGES = [
  "https://images.unsplash.com/photo-1600596542815-e32c215dd86d?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80",
];

export default function ListingCard({
  property,
  onClick,
  isSelected,
}: ListingCardProps) {
  const tags = getCleanTags(
    property.features || (property as any).vibe_features
  );

  const safeId = Number(property.id) || 0;
  const fallbackImage = STOCK_IMAGES[safeId % STOCK_IMAGES.length];

  const primaryImage =
    property.cover_image_url || property.image_urls?.[0] || fallbackImage;
  const [imgSrc, setImgSrc] = useState(primaryImage);

  useEffect(() => {
    setImgSrc(primaryImage);
  }, [primaryImage, property.id]);

  const formattedPrice = new Intl.NumberFormat("en-GH", {
    style: "decimal",
    maximumFractionDigits: 0,
  }).format(property.price);

  const currencySymbol = property.currency === "USD" ? "$" : "₵";

  return (
    <motion.div
      layoutId={`card-${property.id}`}
      onClick={onClick}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ scale: 1.02 }}
      className={`
        relative mb-4 rounded-xl overflow-hidden cursor-pointer group transition-all duration-300
        ${
          isSelected
            ? "ring-2 ring-emerald-500 shadow-2xl shadow-emerald-900/20 bg-white/10"
            : "bg-white/5 border border-white/10 hover:border-white/20 hover:bg-white/10"
        }
      `}
    >
      <div className="h-32 w-full relative overflow-hidden bg-gray-900">
        <img
          src={imgSrc}
          alt={property.title}
          onError={() => setImgSrc(fallbackImage)}
          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110 opacity-90 group-hover:opacity-100"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent" />

        <div className="absolute bottom-3 left-3 z-10">
          <p className="text-white font-mono font-bold text-lg tracking-tight drop-shadow-md">
            <span className="text-emerald-400 mr-0.5">{currencySymbol}</span>
            {formattedPrice}
          </p>
        </div>

        <div className="absolute top-3 right-3 z-10">
          <span
            className={`
            px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider text-black shadow-lg
            ${property.type === "rent" ? "bg-blue-400" : "bg-emerald-400"}
          `}
          >
            {property.type}
          </span>
        </div>
      </div>

      <div className="p-4">
        <h3 className="text-white font-bold text-sm leading-snug mb-1 line-clamp-1 group-hover:text-emerald-400 transition-colors">
          {property.title}
        </h3>

        <div className="flex items-center gap-1.5 mb-3">
          <MapPin size={12} className="text-gray-500" />
          <p className="text-gray-400 text-xs font-medium truncate">
            {property.location_name || "Unmapped Location"}
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {tags.map((tag, i) => (
            <span
              key={i}
              className="px-1.5 py-0.5 rounded-md bg-white/5 border border-white/10 text-[9px] text-gray-300 font-medium uppercase tracking-wide group-hover:border-white/20 transition-colors"
            >
              {tag}
            </span>
          ))}
        </div>

        <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
          <div className="bg-emerald-500 rounded-full p-1.5 text-black shadow-lg">
            <ArrowRight size={12} />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
