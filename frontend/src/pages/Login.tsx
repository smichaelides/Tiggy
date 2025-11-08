import { useState } from "react";
// import { useNavigate } from "react-router-dom";
import { useGoogleLogin } from "@react-oauth/google";
import tigerAvatar from "../assets/tiggy.png";
import princetonLogo from "../assets/princeton.png";
import { authAPI } from "../api/authAPI";

interface LoginProps {
  setIsAuthenticated: (isAuth: boolean) => void;
  setHasCompletedWelcome: (completedWelcome: boolean) => void;
}

function Login({ setIsAuthenticated, setHasCompletedWelcome }: LoginProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Must separate as useGoogleLogin is a hook.
  const login = useGoogleLogin({
    onSuccess: async (tokenResponse) => {

      try {
        const userInfo = await authAPI.googleLogin(tokenResponse.access_token);
        const loginResponse = await authAPI.login(userInfo.email);
        setIsAuthenticated(true);
      } catch (ex) {
        console.error(ex);
        if (ex?.message) {
          setIsAuthenticated(true);
          setHasCompletedWelcome(false);
        }
      }
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
