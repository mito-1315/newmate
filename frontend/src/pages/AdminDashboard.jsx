import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Plus, 
  Users, 
  CheckCircle, 
  Clock, 
  AlertTriangle,
  BarChart3,
  Upload,
  QrCode,
  Download,
  Send,
  Building,
  GraduationCap,
  Award
} from 'lucide-react';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState({
    total_certificates: 0,
    issued_today: 0,
    pending_verifications: 0,
    verification_rate: 0
  });

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await fetch('/analytics/verification-stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BarChart3 },
    { id: 'issue', name: 'Issue Certificates', icon: Plus },
    { id: 'legacy', name: 'Legacy Verification', icon: Users },
    { id: 'reports', name: 'Reports', icon: FileText },
  ];

  const statCards = [
    {
      title: 'Total Certificates',
      value: stats.total_certificates || 0,
      icon: FileText,
      color: 'bg-blue-500',
      change: '+12%'
    },
    {
      title: 'Issued Today',
      value: stats.issued_today || 0,
      icon: Plus,
      color: 'bg-green-500',
      change: '+5%'
    },
    {
      title: 'Pending Verifications',
      value: stats.pending_verifications || 0,
      icon: Clock,
      color: 'bg-yellow-500',
      change: '-2%'
    },
    {
      title: 'Verification Rate',
      value: `${Math.round((stats.verification_rate || 0) * 100)}%`,
      icon: CheckCircle,
      color: 'bg-purple-500',
      change: '+3%'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Building className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">
                University Admin Dashboard
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Welcome, Admin</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4 inline mr-2" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {statCards.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <div key={index} className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                      <div className={`p-3 rounded-full ${stat.color}`}>
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-500">{stat.title}</p>
                        <p className="text-2xl font-semibold text-gray-900">
                          {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
                        </p>
                        <p className="text-sm text-green-600">{stat.change}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={() => setActiveTab('issue')}
                  className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Plus className="h-8 w-8 text-blue-600 mr-3" />
                  <div className="text-left">
                    <div className="font-medium text-gray-900">Issue New Certificate</div>
                    <div className="text-sm text-gray-500">Generate digital certificate with QR code</div>
                  </div>
                </button>

                <button
                  onClick={() => setActiveTab('legacy')}
                  className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Users className="h-8 w-8 text-green-600 mr-3" />
                  <div className="text-left">
                    <div className="font-medium text-gray-900">Review Legacy Certificates</div>
                    <div className="text-sm text-gray-500">Verify and approve legacy requests</div>
                  </div>
                </button>

                <button
                  className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Upload className="h-8 w-8 text-purple-600 mr-3" />
                  <div className="text-left">
                    <div className="font-medium text-gray-900">Bulk Upload</div>
                    <div className="text-sm text-gray-500">Upload certificates from ERP/CSV</div>
                  </div>
                </button>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <div className="flex items-center">
                    <div className="p-2 bg-green-100 rounded-full">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Certificate issued for John Doe</p>
                      <p className="text-sm text-gray-500">Computer Science - 2023</p>
                    </div>
                  </div>
                  <span className="text-sm text-gray-500">2 minutes ago</span>
                </div>

                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <div className="flex items-center">
                    <div className="p-2 bg-yellow-100 rounded-full">
                      <Clock className="h-4 w-4 text-yellow-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Legacy verification pending</p>
                      <p className="text-sm text-gray-500">Jane Smith - Engineering</p>
                    </div>
                  </div>
                  <span className="text-sm text-gray-500">1 hour ago</span>
                </div>

                <div className="flex items-center justify-between py-3">
                  <div className="flex items-center">
                    <div className="p-2 bg-blue-100 rounded-full">
                      <QrCode className="h-4 w-4 text-blue-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Certificate verified by employer</p>
                      <p className="text-sm text-gray-500">ABC Company verified CS certificate</p>
                    </div>
                  </div>
                  <span className="text-sm text-gray-500">3 hours ago</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'issue' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Issue New Certificate</h3>
              <p className="mt-1 text-sm text-gray-500">
                Enter student details to generate a digital certificate with QR code
              </p>
            </div>
            <div className="p-6">
              <div className="text-center py-12">
                <Plus className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">Certificate Issuance Form</h3>
                <p className="mt-1 text-sm text-gray-500">
                  This will redirect to the detailed certificate issuance page
                </p>
                <div className="mt-6">
                  <a
                    href="/admin/issue-certificate"
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Go to Certificate Issuance
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'legacy' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Legacy Certificate Verification</h3>
              <p className="mt-1 text-sm text-gray-500">
                Review and verify legacy certificate requests from students
              </p>
            </div>
            <div className="p-6">
              <div className="text-center py-12">
                <Users className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">Legacy Verification Queue</h3>
                <p className="mt-1 text-sm text-gray-500">
                  This will redirect to the legacy verification management page
                </p>
                <div className="mt-6">
                  <a
                    href="/admin/legacy-verification"
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    <Users className="h-4 w-4 mr-2" />
                    Go to Legacy Verification
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Reports & Analytics</h3>
              <p className="mt-1 text-sm text-gray-500">
                View detailed reports and analytics for certificate management
              </p>
            </div>
            <div className="p-6">
              <div className="text-center py-12">
                <FileText className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">Reports Coming Soon</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Detailed analytics and reporting features will be available soon
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;