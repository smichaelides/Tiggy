import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { GoogleOAuthProvider } from "@react-oauth/google";


createRoot(document.getElementById("root")!).render(
  // <StrictMode>
  <GoogleOAuthProvider clientId="280285444479-5f2hkpe9iabj5alrbrvdkd4g9lcqdlph.apps.googleusercontent.com">
    <App />
  </GoogleOAuthProvider>
  // </StrictMode>,
);
