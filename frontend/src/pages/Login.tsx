import { useState } from "react";
import { useNavigate } from "react-router-dom";
import princetonLogo from "../assets/princeton.png";
import tigerAvatar from "../assets/tiggy.png";

function Login() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleLogin = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const oauth2Endpoint = "https://accounts.google.com/o/oauth2/v2/auth";
      const body = {
        "method": "GET",
        "action": oauth2Endpoint,
      }

      const params = {
        client_id:
          "280285444479-5f2hkpe9iabj5alrbrvdkd4g9lcqdlph.apps.googleusercontent.com",
        redirect_uri: "https://localhost:5173/callback",
        response_type: "token",
        scope:
          "https://www.googleapis.com/auth/drive.metadata.readonly https://www.googleapis.com/auth/calendar.readonly",
        include_granted_scopes: "true",
        state: "pass-through value",
      };

      fetch(oauth2Endpoint, params);
      


    } catch (error) {
      console.error("Failed to login:", error);
      setError("Failed to login. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <img src={princetonLogo} alt="Princeton" className="login-logo" />
          <div className="login-title-container">
            <h1 className="login-title">Meet Tiggy</h1>
            <img src={tigerAvatar} alt="Tiggy" className="login-tiggy" />
          </div>
          <p className="login-subtitle">Your Princeton AI assistant</p>
        </div>

        <div className="login-content">
          {error && <div className="error-message">{error}</div>}

          <button
            onClick={handleLogin}
            className="login-button"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Creating account..." : "Get Started"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Login;
