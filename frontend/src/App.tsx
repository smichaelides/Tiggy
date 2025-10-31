
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import MainPage from './pages/MainPage';
import LoginPage from './pages/Login';
import SettingsPage from './pages/Settings';
import Callback from './pages/Callback';
import './App.css';

function App() {
  const [isAuthenticated] = useState(true);

  return (
    <Router>
      <Routes>
        <Route path="/callback" element={<Callback />} />
        <Route 
          path="/login" 
          element={
            !isAuthenticated ? (
              <LoginPage />
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
            isAuthenticated ? (
              <MainPage />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
