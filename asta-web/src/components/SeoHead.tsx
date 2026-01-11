import { Helmet } from 'react-helmet-async';

interface SeoHeadProps {
  title: string;
  description?: string;
  location?: string;
}

export default function SeoHead({ title, description = '', location = '' }: SeoHeadProps) {
  const fullTitle = `${title} | Asta`;
  const fullDescription =
    description ||
    `Explore verified real estate listings, market trends, and geospatial insights across ${location || 'Ghana'} with Asta — Ghana's intelligent property platform.`;

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={fullDescription} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={fullDescription} />
      <meta property="og:type" content="website" />
      <meta property="og:url" content={window.location.href} />
      <meta name="twitter:card" content="summary_large_image" />
    </Helmet>
  );
}
