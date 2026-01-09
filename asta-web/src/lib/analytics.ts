import ReactGA from "react-ga4";

// 1. Initialize GA4 with your specific Measurement ID
export const initGA = () => {
  ReactGA.initialize("G-8VRMDE51Q1"); // Your ID
};

// 2. Track Page Views (The SPA Fix)
export const trackPageView = (path: string) => {
  ReactGA.send({ hitType: "pageview", page: path });
};

// 3. Track Specific User Actions (Conversion Events)
export const trackEvent = (category: string, action: string, label?: string) => {
  ReactGA.event({
    category,
    action,
    label,
  });
};
