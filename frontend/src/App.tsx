import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate,
} from "react-router-dom";
import { useState } from "react";
import MainPage from "./pages/MainPage";
import LoginPage from "./pages/Login";
import SettingsPage from "./pages/Settings";
import WelcomePage from "./pages/Welcome";
import type { OnboardingInfo } from "./types";
import CourseRecs from "./pages/CourseRecs";
import { authAPI } from "./api/authAPI";
import "./App.css";

function AppContent() {
  const [hasCompletedWelcome, setHasCompletedWelcome] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [onboardingInfo, setOnboardingInfo] = useState<OnboardingInfo>({});
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      setIsAuthenticated(false);
      setOnboardingInfo({});
      setHasCompletedWelcome(true);
      navigate("/login");
    }
  };

  return (
    <Routes>
      <Route
        path="/login"
        element={
          !isAuthenticated ? (
            <LoginPage
              setIsAuthenticated={setIsAuthenticated}
              setHasCompletedWelcome={setHasCompletedWelcome}
              setOnboardingInfo={setOnboardingInfo}
            />
          ) : !hasCompletedWelcome ? (
            <WelcomePage googleAuthInfo={onboardingInfo} />
          ) : (
            <Navigate to="/" replace />
          )
        }
      />
      <Route
        path="/settings"
        element={
          isAuthenticated ? (
            <SettingsPage onLogout={handleLogout} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/course-recs"
        element={
          isAuthenticated ? (
            <CourseRecs onLogout={handleLogout} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/"
        element={
          isAuthenticated ? (
            <MainPage onLogout={handleLogout} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
