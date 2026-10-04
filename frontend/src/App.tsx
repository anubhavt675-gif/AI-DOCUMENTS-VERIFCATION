import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import DocumentDetail from './pages/DocumentDetail';
import { MLAnomalyDashboard } from './pages/MLAnomalyDashboard';
import DemoTamperPage from './pages/DemoTamperPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="gov-app-shell">
        <Header />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route
            path="/ml"
            element={
              <main className="container page">
                <MLAnomalyDashboard />
              </main>
            }
          />
          <Route path="/demo" element={<DemoTamperPage />} />
          <Route path="/documents/:documentId" element={<DocumentDetail />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
