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
      const callbackUrl = `${window.location.origin}/callback`;
      console.log('Login button clicked, redirecting with:', {
        returnTo: "/",
        callbackUrl
      });
      navigate("/callback");
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
