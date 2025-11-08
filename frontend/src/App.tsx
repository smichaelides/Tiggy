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
import "./App.css";

function App() {
  const [hasCompletedWelcome, setHasCompletedWelcome] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

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
              />
            ) : !hasCompletedWelcome ? (
              <WelcomePage />
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
