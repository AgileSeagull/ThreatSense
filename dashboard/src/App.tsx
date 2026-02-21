import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { Activity } from './pages/Activity';
import { Alerts } from './pages/Alerts';
import { AlertDetail } from './pages/AlertDetail';
import './index.css';

function NavBar() {
  const location = useLocation();

  return (
    <header className="sticky top-0 z-10 border-b border-gray-200 bg-white">
      <div className="flex items-center gap-6 px-4 py-3">
        <Link to="/" className="text-lg font-semibold text-gray-800 tracking-tight hover:text-gray-900">
          Threat Detection
        </Link>
        <nav className="flex items-center gap-1">
          <Link
            to="/"
            className={`px-3 py-2 text-sm font-medium rounded ${
              location.pathname === '/' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Dashboard
          </Link>
          <Link
            to="/activity"
            className={`px-3 py-2 text-sm font-medium rounded ${
              location.pathname === '/activity' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Events
          </Link>
          <Link
            to="/alerts"
            className={`px-3 py-2 text-sm font-medium rounded ${
              location.pathname.startsWith('/alerts') ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Alerts
          </Link>
        </nav>
      </div>
    </header>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 text-gray-800">
        <NavBar />
        <main className="p-4 md:p-6 max-w-[1600px] mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/activity" element={<Activity />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/alerts/:id" element={<AlertDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
