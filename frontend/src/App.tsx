import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { DataInventory } from './pages/DataInventory';
import { RecordDetails } from './pages/RecordDetails';
import { ExpiryManagement } from './pages/ExpiryManagement';
import { PurposeMismatch } from './pages/PurposeMismatch';
import { AIInsights } from './pages/AIInsights';
import { PolicyManagement } from './pages/PolicyManagement';
import { AuditTrail } from './pages/AuditTrail';

export const App: React.FC = () => {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inventory" element={<DataInventory />} />
          <Route path="/records" element={<RecordDetails />} />
          <Route path="/expiry" element={<ExpiryManagement />} />
          <Route path="/purpose-mismatch" element={<PurposeMismatch />} />
          <Route path="/ai-insights" element={<AIInsights />} />
          <Route path="/policy" element={<PolicyManagement />} />
          <Route path="/audit" element={<AuditTrail />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
