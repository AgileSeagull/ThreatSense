import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { Activity } from './pages/Activity';
import { Alerts } from './pages/Alerts';
import { AlertDetail } from './pages/AlertDetail';
import { Sensors } from './pages/Sensors';
import './index.css';

function NavBar() {
  const location = useLocation();

  const link = (to: string, label: string, exact = false) => {
    const active = exact ? location.pathname === to : location.pathname.startsWith(to);
    return (
      <Link
        to={to}
        className={`px-3 py-2 text-sm font-medium rounded transition-colors ${
          active
            ? 'bg-teal-700 text-white'
            : 'text-teal-100 hover:bg-teal-700 hover:text-white'
        }`}
      >
        {label}
      </Link>
    );
  };

  return (
    <header className="sticky top-0 z-10 bg-gradient-to-r from-teal-900 to-teal-700 shadow-md">
      <div className="flex items-center gap-6 px-5 py-3 max-w-[1600px] mx-auto">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-2 shrink-0">
          <span className="text-white text-xl font-bold tracking-tight">Threat Detection</span>
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-1">
          {link('/', 'Overview', true)}
          {link('/activity', 'Incident Log')}
          {link('/alerts', 'Clinical Alerts')}
          {link('/sensors', 'Vital Sensors')}
        </nav>

        {/* Status pill */}
        <div className="ml-auto flex items-center gap-1.5 text-xs text-teal-200 shrink-0">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Live monitoring
        </div>
      </div>
    </header>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 text-gray-800">
        <NavBar />
        <main className="p-4 md:p-6 max-w-[1600px] mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/activity" element={<Activity />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/alerts/:id" element={<AlertDetail />} />
            <Route path="/sensors" element={<Sensors />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
