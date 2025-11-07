import { useState } from "react";
// import { useNavigate } from "react-router-dom";
import { useGoogleLogin } from "@react-oauth/google";
import tigerAvatar from "../assets/tiggy.png";
import princetonLogo from "../assets/princeton.png";

function Login() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // const navigate = useNavigate();

  const login = useGoogleLogin({
    onSuccess: (tokenResponse) => {
      console.log(tokenResponse);
    },
  });

  const handleLogin = async () => {
    setIsSubmitting(true);
    setError(null);
    login();
  }

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
