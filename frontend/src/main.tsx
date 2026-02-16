import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { GoogleOAuthProvider } from "@react-oauth/google";

// Get Google Client ID from environment variable or use default
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || 
  "280285444479-5f2hkpe9iabj5alrbrvdkd4g9lcqdlph.apps.googleusercontent.com";

createRoot(document.getElementById("root")!).render(
  // <StrictMode>
  <GoogleOAuthProvider clientId={googleClientId}>
    <App />
  </GoogleOAuthProvider>
  // </StrictMode>,
);
