import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Users, 
  Shield, 
  AlertTriangle, 
  TrendingUp, 
  Building2, 
  Eye, 
  Ban,
  CheckCircle,
  XCircle,
  Clock,
  Activity
} from 'lucide-react';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [verificationTrends, setVerificationTrends] = useState(null);
  const [institutions, setInstitutions] = useState({});
  const [blacklist, setBlacklist] = useState({ blacklisted_certificates: [], blacklisted_ips: [] });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch all dashboard data in parallel
      const [statsRes, activityRes, trendsRes, institutionsRes, blacklistRes] = await Promise.all([
        fetch('/admin/dashboard/stats'),
        fetch('/admin/dashboard/recent-activity'),
        fetch('/admin/dashboard/verification-trends'),
        fetch('/admin/dashboard/institutions'),
        fetch('/admin/dashboard/blacklist')
      ]);

      const [statsData, activityData, trendsData, institutionsData, blacklistData] = await Promise.all([
        statsRes.json(),
        activityRes.json(),
        trendsRes.json(),
        institutionsRes.json(),
        blacklistRes.json()
      ]);

      setStats(statsData);
      setRecentActivity(activityData.activities || []);
      setVerificationTrends(trendsData);
      setInstitutions(institutionsData.institutions || {});
      setBlacklist(blacklistData);
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBlacklistCertificate = async (certificateId) => {
    const reason = prompt('Enter reason for blacklisting:');
    if (reason) {
      try {
        const response = await fetch('/admin/dashboard/blacklist-certificate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ certificate_id: certificateId, reason })
        });
        
        if (response.ok) {
          alert('Certificate blacklisted successfully');
          fetchDashboardData(); // Refresh data
        }
      } catch (error) {
        console.error('Failed to blacklist certificate:', error);
      }
    }
  };

  const handleBlacklistIP = async (ipAddress) => {
    const reason = prompt('Enter reason for blacklisting IP:');
    if (reason) {
      try {
        const response = await fetch('/admin/dashboard/blacklist-ip', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ip_address: ipAddress, reason })
        });
        
        if (response.ok) {
          alert('IP blacklisted successfully');
          fetchDashboardData(); // Refresh data
        }
      } catch (error) {
        console.error('Failed to blacklist IP:', error);
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="mt-2 text-gray-600">Monitor verification activity, detect fraud, and manage the system</p>
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              href="/admin/issue-certificate"
              className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow border border-gray-200"
            >
              <div className="flex items-center">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                  </svg>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-gray-900">Issue Certificate</h3>
                  <p className="text-sm text-gray-500">Create new certificates</p>
                </div>
              </div>
            </a>

            <a
              href="/admin/legacy-verification"
              className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow border border-gray-200"
            >
              <div className="flex items-center">
                <div className="p-3 bg-green-100 rounded-lg">
                  <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-gray-900">Legacy Verification</h3>
                  <p className="text-sm text-gray-500">Review pending requests</p>
                </div>
              </div>
            </a>

            <a
              href="/admin/dashboard"
              className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow border border-gray-200 bg-blue-50"
            >
              <div className="flex items-center">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                  </svg>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-gray-900">Dashboard</h3>
                  <p className="text-sm text-gray-500">View analytics & monitoring</p>
                </div>
              </div>
            </a>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', name: 'Overview', icon: BarChart3 },
              { id: 'activity', name: 'Recent Activity', icon: Activity },
              { id: 'trends', name: 'Fraud Detection', icon: TrendingUp },
              { id: 'institutions', name: 'Institutions', icon: Building2 },
              { id: 'blacklist', name: 'Blacklist', icon: Shield }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="h-4 w-4 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && stats && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Users className="h-6 w-6 text-blue-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Total Certificates</dt>
                        <dd className="text-lg font-medium text-gray-900">{stats.total_certificates}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Successful Verifications</dt>
                        <dd className="text-lg font-medium text-gray-900">{stats.successful_verifications}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <XCircle className="h-6 w-6 text-red-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Failed Verifications</dt>
                        <dd className="text-lg font-medium text-gray-900">{stats.failed_verifications}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <TrendingUp className="h-6 w-6 text-purple-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Success Rate</dt>
                        <dd className="text-lg font-medium text-gray-900">{stats.verification_success_rate}%</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity Summary */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Recent Activity (Last 30 Days)</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{stats.recent_certificates}</div>
                    <div className="text-sm text-gray-500">New Certificates</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{stats.recent_verifications}</div>
                    <div className="text-sm text-gray-500">Verification Attempts</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{stats.unique_institutions}</div>
                    <div className="text-sm text-gray-500">Active Institutions</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Recent Activity Tab */}
        {activeTab === 'activity' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent System Activity</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {recentActivity.map((activity, index) => (
                <div key={index} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      {activity.type === 'certificate_issued' ? (
                        <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                      ) : (
                        <Eye className="h-5 w-5 text-blue-500 mr-3" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {activity.type === 'certificate_issued' 
                            ? `Certificate issued: ${activity.data.certificate_id}`
                            : `Verification attempt: ${activity.data.status}`
                          }
                        </p>
                        <p className="text-sm text-gray-500">
                          {activity.type === 'certificate_issued' 
                            ? `${activity.data.student_name} - ${activity.data.institution}`
                            : `IP: ${activity.data.ip_address}`
                          }
                        </p>
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      {new Date(activity.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Fraud Detection Tab */}
        {activeTab === 'trends' && verificationTrends && (
          <div className="space-y-6">
            {/* Suspicious Activity Alerts */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <div className="flex items-center">
                <AlertTriangle className="h-6 w-6 text-red-600 mr-3" />
                <h3 className="text-lg font-medium text-red-800">Suspicious Activity Detected</h3>
              </div>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-red-700">Suspicious IPs: {verificationTrends.suspicious_ips.length}</p>
                  <p className="text-sm text-red-700">Suspicious User Agents: {verificationTrends.suspicious_user_agents.length}</p>
                </div>
                <div>
                  <p className="text-sm text-red-700">Total Failed Attempts: {verificationTrends.total_failed_attempts}</p>
                </div>
              </div>
            </div>

            {/* Most Common IPs */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Most Common IP Addresses</h3>
              </div>
              <div className="divide-y divide-gray-200">
                {verificationTrends.most_common_ips.map(([ip, count], index) => (
                  <div key={index} className="px-6 py-3 flex justify-between items-center">
                    <span className="text-sm font-mono text-gray-900">{ip}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">{count} attempts</span>
                      <button
                        onClick={() => handleBlacklistIP(ip)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        <Ban className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Institutions Tab */}
        {activeTab === 'institutions' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Institution Statistics</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {Object.entries(institutions).map(([institution, data]) => (
                <div key={institution} className="px-6 py-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{institution}</h4>
                      <p className="text-sm text-gray-500">
                        {data.total_certificates} total certificates, {data.recent_certificates} recent
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-500">Status Breakdown:</div>
                      <div className="flex space-x-4 text-xs">
                        <span className="text-green-600">Issued: {data.status_breakdown.issued}</span>
                        <span className="text-blue-600">Verified: {data.status_breakdown.verified}</span>
                        <span className="text-red-600">Revoked: {data.status_breakdown.revoked}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Blacklist Tab */}
        {activeTab === 'blacklist' && (
          <div className="space-y-6">
            {/* Blacklisted Certificates */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Blacklisted Certificates</h3>
              </div>
              <div className="divide-y divide-gray-200">
                {blacklist.blacklisted_certificates.map((cert, index) => (
                  <div key={index} className="px-6 py-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{cert.certificate_id}</p>
                        <p className="text-sm text-gray-500">Reason: {cert.reason}</p>
                        <p className="text-xs text-gray-400">Blacklisted: {new Date(cert.blacklisted_at).toLocaleString()}</p>
                      </div>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Blacklisted
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Blacklisted IPs */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Blacklisted IP Addresses</h3>
              </div>
              <div className="divide-y divide-gray-200">
                {blacklist.blacklisted_ips.map((ip, index) => (
                  <div key={index} className="px-6 py-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-sm font-mono text-gray-900">{ip.ip_address}</p>
                        <p className="text-sm text-gray-500">Reason: {ip.reason}</p>
                        <p className="text-xs text-gray-400">Blacklisted: {new Date(ip.blacklisted_at).toLocaleString()}</p>
                      </div>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Blacklisted
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;