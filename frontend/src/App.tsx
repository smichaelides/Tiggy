import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { useState } from "react";
import MainPage from "./pages/MainPage";
import LoginPage from "./pages/Login";
import SettingsPage from "./pages/Settings";
import WelcomePage from "./pages/Welcome";
import type { OnboardingInfo } from "./types";
import "./App.css";

function App() {
  const [hasCompletedWelcome, setHasCompletedWelcome] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [onboardingInfo, setOnboardingInfo] = useState<OnboardingInfo>({});

  return (
    <Router>
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
              <SettingsPage />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/"
          element={
            isAuthenticated ? <MainPage /> : <Navigate to="/login" replace />
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
