import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { FileText, BarChart3, Users, Menu, X, Plus } from 'lucide-react';
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import ManualReview from './pages/ManualReview';
import CertificateIssuance from './pages/CertificateIssuance';
import PublicVerification from './pages/PublicVerification';

function App() {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const navigation = [
    { name: 'Verify', href: '/', icon: FileText },
    { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
    { name: 'Reviews', href: '/reviews', icon: Users },
    { name: 'Issue', href: '/issue', icon: Plus },
  ];

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <FileText className="h-8 w-8 text-blue-600" />
                  <span className="ml-2 text-xl font-bold text-gray-900">
                    Certificate Verifier
                  </span>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  {navigation.map((item) => {
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.name}
                        to={item.href}
                        className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 hover:text-blue-600 transition-colors"
                      >
                        <Icon className="h-4 w-4 mr-2" />
                        {item.name}
                      </Link>
                    );
                  })}
                </div>
              </div>

              {/* Mobile menu button */}
              <div className="sm:hidden">
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 transition-colors"
                >
                  {mobileMenuOpen ? (
                    <X className="h-6 w-6" />
                  ) : (
                    <Menu className="h-6 w-6" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Mobile menu */}
          {mobileMenuOpen && (
            <div className="sm:hidden">
              <div className="pt-2 pb-3 space-y-1">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className="flex items-center px-3 py-2 text-base font-medium text-gray-900 hover:bg-gray-50 transition-colors"
                    >
                      <Icon className="h-5 w-5 mr-3" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            </div>
          )}
        </nav>

        {/* Main content */}
        <main>
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/reviews" element={<ManualReview />} />
            <Route path="/issue" element={<CertificateIssuance />} />
            <Route path="/verify/:attestationId" element={<PublicVerification />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-auto">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-4">
                <FileText className="h-6 w-6 text-gray-400" />
                <span className="text-gray-500 text-sm">
                  Certificate Verifier © 2023
                </span>
              </div>
              <div className="flex space-x-6">
                <a href="/docs" className="text-gray-500 hover:text-gray-700 text-sm">
                  Documentation
                </a>
                <a href="/api" className="text-gray-500 hover:text-gray-700 text-sm">
                  API
                </a>
                <a href="/support" className="text-gray-500 hover:text-gray-700 text-sm">
                  Support
                </a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

const NotFound = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
      <p className="text-gray-600 mb-4">Page not found</p>
      <Link
        to="/"
        className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
      >
        <FileText className="h-4 w-4 mr-2" />
        Go Home
      </Link>
    </div>
  </div>
);

export default App;
