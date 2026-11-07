import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Requirements } from './pages/Requirements';
import { Artifacts } from './pages/Artifacts';
import { TraceabilityGraph } from './pages/TraceabilityGraph';
import { ChangeRequests } from './pages/ChangeRequests';
import { ImpactAnalysisView } from './pages/ImpactAnalysisView';
import { RemediationTracker } from './pages/RemediationTracker';
import { Reports } from './pages/Reports';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/requirements" element={<Requirements />} />
            <Route path="/artifacts" element={<Artifacts />} />
            <Route path="/graph" element={<TraceabilityGraph />} />
            <Route path="/change-requests" element={<ChangeRequests />} />
            <Route path="/change-requests/:id" element={<ImpactAnalysisView />} />
            <Route path="/remediation" element={<RemediationTracker />} />
            <Route path="/reports" element={<Reports />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};
export default App;
