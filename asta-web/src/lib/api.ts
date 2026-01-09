// This file automatically determines if we are on Localhost or in the Cloud

const CLOUD_URL = "https://asta-engine-dev-1074257837836.us-central1.run.app";
const LOCAL_URL = "http://127.0.0.1:8080";

export const API_BASE_URL = import.meta.env.PROD ? CLOUD_URL : LOCAL_URL;

console.log(`🔌 ASTA API CONNECTED: ${API_BASE_URL}`);
