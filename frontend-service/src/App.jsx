import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import { useAuthStore } from './store/authStore';
import TextEntryPage from './pages/TextEntryPage';

// New component imports for the resume builder feature
import TemplatesPage from './pages/TemplatesPage';
import ResumeBuilderPage from './pages/ResumeBuilderPage';

const ProtectedRoute = ({ children }) => {
  const token = useAuthStore((state) => state.token);
  return token ? children : <Navigate to="/login" />;
};

const App = () => {
  const init = useAuthStore((state) => state.init);

  useEffect(() => {
    init(); // load token from localStorage into Zustand
  }, [init]);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<Navigate to="/dashboard" />} />

        {/* Protected routes */}
        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/text-entry/:templateId" element={<ProtectedRoute><TextEntryPage /></ProtectedRoute>} />

        {/* Resume builder routes */}
        <Route path="/templates" element={<ProtectedRoute><TemplatesPage /></ProtectedRoute>} />
        <Route path="/builder/:templateId" element={<ProtectedRoute><ResumeBuilderPage /></ProtectedRoute>} />
      </Routes>
    </Router>
  );
};

export default App;
