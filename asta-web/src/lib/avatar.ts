/**
 * Generates a deterministic avatar URL based on a seed string (name/ID).
 * Using DiceBear API which is free and high-performance.
 */
export function getAvatarUrl(seed: string, style: 'bottts' | 'shapes' | 'identicon' = 'bottts'): string {
  // Clean the seed to ensure consistency
  const safeSeed = encodeURIComponent(seed.trim() || 'agent');
  
  // 'bottts' = Robot style (Fits Asta Scout theme)
  // 'shapes' = Abstract geometric (Fits Corporate/Pro theme)
  return `https://api.dicebear.com/7.x/${style}/svg?seed=${safeSeed}&backgroundColor=transparent`;
}
