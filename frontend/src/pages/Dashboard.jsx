import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, ScatterChart, Scatter
} from 'recharts';
import { 
  FileText, CheckCircle, XCircle, Clock,
  TrendingUp, Users, Award, Shield, Eye, Layers
} from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_verifications: 0,
    successful_verifications: 0,
    failed_verifications: 0,
    verification_rate: 0.0,
    period: "30_days",
    risk_distribution: [],
    daily_verifications: [],
    institution_stats: [],
    layer_performance: [],
    forensic_detections: [],
    recent_verifications: []
  });
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d'); // 7d, 30d, 90d
  const [selectedVerification, setSelectedVerification] = useState(null);
  const [showLayerDetails, setShowLayerDetails] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/analytics/verification-stats');
        if (response.ok) {
          const data = await response.json();
          setStats(prevStats => ({
            ...prevStats,
            ...data
          }));
        } else {
          console.error('Failed to fetch stats:', response.statusText);
        }
      } catch (err) {
        console.error('Error fetching stats:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [timeRange]);



  const statCards = [
    {
      title: 'Total Verifications',
      value: stats.total_verifications || 0,
      icon: FileText,
      color: 'bg-blue-500',
      change: '+12%'
    },
    {
      title: 'Successful Verifications',
      value: stats.successful_verifications || 0,
      icon: CheckCircle,
      color: 'bg-green-500',
      change: '+8%'
    },
    {
      title: 'Failed Verifications',
      value: stats.failed_verifications || 0,
      icon: Shield,
      color: 'bg-red-500',
      change: '-15%'
    },
    {
      title: 'Verification Rate',
      value: Math.round((stats.verification_rate || 0) * 100),
      icon: Clock,
      color: 'bg-yellow-500',
      change: '+5%'
    }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
            <p className="text-gray-600">Certificate verification analytics and insights</p>
          </div>
          
          <div className="mt-4 md:mt-0">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statCards.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div key={index} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">{stat.title}</p>
                    <p className="text-2xl font-bold text-gray-900">{(stat.value || 0).toLocaleString()}</p>
                    <div className="flex items-center mt-2">
                      <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                      <span className="text-sm text-green-600">{stat.change}</span>
                      <span className="text-sm text-gray-500 ml-1">vs last period</span>
                    </div>
                  </div>
                  <div className={`${stat.color} rounded-lg p-3`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Enhanced Analytics Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* 3-Layer Performance Chart */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">3-Layer Performance</h3>
              <button
                onClick={() => setShowLayerDetails(!showLayerDetails)}
                className="text-blue-600 hover:text-blue-700 text-sm flex items-center"
              >
                <Layers className="h-4 w-4 mr-1" />
                {showLayerDetails ? 'Hide' : 'Show'} Details
              </button>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { layer: 'Layer 1\nExtraction', success_rate: 92, avg_time: 1.2 },
                { layer: 'Layer 2\nForensics', success_rate: 88, avg_time: 2.8 },
                { layer: 'Layer 3\nSignatures', success_rate: 85, avg_time: 1.5 },
                { layer: 'QR\nIntegrity', success_rate: 96, avg_time: 0.3 }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="layer" />
                <YAxis />
                <Tooltip formatter={(value, name) => [
                  name === 'success_rate' ? `${value}%` : `${value}s`,
                  name === 'success_rate' ? 'Success Rate' : 'Avg Time'
                ]} />
                <Bar dataKey="success_rate" fill="#10b981" name="Success Rate" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Forensic Detection Chart */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Forensic Detections</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Copy-Move', value: 12, color: '#ef4444' },
                    { name: 'Double Compression', value: 8, color: '#f97316' },
                    { name: 'Noise Inconsistency', value: 5, color: '#eab308' },
                    { name: 'Hash Mismatch', value: 3, color: '#dc2626' },
                    { name: 'Clean Images', value: 872, color: '#10b981' }
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => percent > 5 ? `${name} ${(percent * 100).toFixed(0)}%` : ''}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {[
                    { name: 'Copy-Move', value: 12, color: '#ef4444' },
                    { name: 'Double Compression', value: 8, color: '#f97316' },
                    { name: 'Noise Inconsistency', value: 5, color: '#eab308' },
                    { name: 'Hash Mismatch', value: 3, color: '#dc2626' },
                    { name: 'Clean Images', value: 872, color: '#10b981' }
                  ].map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Distribution and Daily Trends */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Daily Verifications with Risk Overlay */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Daily Verifications & Risk Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={stats.daily_verifications}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="verifications" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                  name="Total Verifications"
                />
                <Line 
                  type="monotone" 
                  dataKey="high_risk" 
                  stroke="#ef4444" 
                  strokeWidth={2}
                  dot={{ fill: '#ef4444' }}
                  name="High Risk"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Risk vs Confidence Scatter */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Risk vs Confidence Analysis</h3>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart data={[
                { risk: 0.1, confidence: 0.95, count: 45 },
                { risk: 0.2, confidence: 0.88, count: 32 },
                { risk: 0.3, confidence: 0.75, count: 28 },
                { risk: 0.4, confidence: 0.65, count: 15 },
                { risk: 0.6, confidence: 0.45, count: 8 },
                { risk: 0.8, confidence: 0.25, count: 3 }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="risk" name="Risk Score" />
                <YAxis dataKey="confidence" name="Confidence" />
                <Tooltip formatter={(value, name) => [
                  name === 'count' ? `${value} certificates` : `${(value * 100).toFixed(0)}%`,
                  name === 'count' ? 'Count' : name
                ]} />
                <Scatter dataKey="count" fill="#8884d8" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Institution Performance */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Institution Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats.institution_stats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="verified" fill="#10b981" name="Verified" />
              <Bar dataKey="failed" fill="#ef4444" name="Failed" />
              <Bar dataKey="pending" fill="#f59e0b" name="Pending" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center mb-4">
              <Shield className="h-8 w-8 text-blue-500 mr-3" />
              <h3 className="text-lg font-medium text-gray-900">Security Status</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Active Attestations</span>
                <span className="font-medium">{stats.active_attestations || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Failed Signatures</span>
                <span className="font-medium text-red-600">{stats.failed_signatures || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Tamper Attempts</span>
                <span className="font-medium text-red-600">{stats.tamper_attempts || 0}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center mb-4">
              <Users className="h-8 w-8 text-green-500 mr-3" />
              <h3 className="text-lg font-medium text-gray-900">User Activity</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Active Users</span>
                <span className="font-medium">{stats.active_users || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">New Registrations</span>
                <span className="font-medium">{stats.new_registrations || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">API Calls Today</span>
                <span className="font-medium">{stats.api_calls_today || 0}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center mb-4">
              <Award className="h-8 w-8 text-purple-500 mr-3" />
              <h3 className="text-lg font-medium text-gray-900">System Health</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Donut Model</span>
                <span className="inline-flex px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                  Online
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Database</span>
                <span className="inline-flex px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                  Healthy
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Storage</span>
                <span className="inline-flex px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                  97% Available
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Recent Activity with Evidence Overlays */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Recent Verifications</h3>
            <div className="flex space-x-2">
              <button
                onClick={() => setSelectedVerification(null)}
                className="text-blue-600 hover:text-blue-700 text-sm flex items-center"
              >
                <Eye className="h-4 w-4 mr-1" />
                Evidence View
              </button>
            </div>
          </div>
          
          <div className="space-y-4">
            {[
              {
                id: 'ver_123',
                student: 'John Doe',
                institution: 'University of Technology',
                course: 'Computer Science',
                status: 'verified',
                risk_level: 'low',
                layers: {
                  extraction: { confidence: 0.95, time: 1.2 },
                  forensics: { tamper_prob: 0.1, time: 2.8 },
                  signatures: { seals: 1, signatures: 1, time: 1.5 }
                },
                timestamp: '2 minutes ago'
              },
              {
                id: 'ver_124',
                student: 'Jane Smith',
                institution: 'Tech Institute',
                course: 'Data Science',
                status: 'requires_review',
                risk_level: 'medium',
                layers: {
                  extraction: { confidence: 0.78, time: 1.8 },
                  forensics: { tamper_prob: 0.3, time: 3.2 },
                  signatures: { seals: 0, signatures: 1, time: 1.1 }
                },
                timestamp: '5 minutes ago'
              },
              {
                id: 'ver_125',
                student: 'Mike Johnson',
                institution: 'Engineering College',
                course: 'Mechanical Engineering',
                status: 'tampered',
                risk_level: 'critical',
                layers: {
                  extraction: { confidence: 0.65, time: 2.1 },
                  forensics: { tamper_prob: 0.85, time: 4.1 },
                  signatures: { seals: 0, signatures: 0, time: 0.9 }
                },
                timestamp: '12 minutes ago'
              }
            ].map((verification, index) => (
              <div 
                key={index} 
                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                  selectedVerification?.id === verification.id 
                    ? 'border-blue-300 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedVerification(verification)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {verification.status === 'verified' && <CheckCircle className="h-5 w-5 text-green-500" />}
                    {verification.status === 'requires_review' && <Clock className="h-5 w-5 text-yellow-500" />}
                    {verification.status === 'tampered' && <Shield className="h-5 w-5 text-red-500" />}
                    
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {verification.student} • {verification.status.replace('_', ' ').toUpperCase()}
                      </p>
                      <p className="text-xs text-gray-500">
                        {verification.institution} • {verification.course}
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                      verification.risk_level === 'low' ? 'bg-green-100 text-green-800' :
                      verification.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {verification.risk_level.toUpperCase()}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">{verification.timestamp}</p>
                  </div>
                </div>

                {/* Layer Performance Details */}
                {selectedVerification?.id === verification.id && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Layer Analysis</h4>
                    <div className="grid grid-cols-3 gap-4 text-xs">
                      <div className="bg-blue-50 p-3 rounded">
                        <div className="font-medium text-blue-900">Layer 1: Extraction</div>
                        <div className="text-blue-700">Confidence: {(verification.layers.extraction.confidence * 100).toFixed(0)}%</div>
                        <div className="text-blue-600">Time: {verification.layers.extraction.time}s</div>
                      </div>
                      
                      <div className="bg-purple-50 p-3 rounded">
                        <div className="font-medium text-purple-900">Layer 2: Forensics</div>
                        <div className="text-purple-700">Tamper: {(verification.layers.forensics.tamper_prob * 100).toFixed(0)}%</div>
                        <div className="text-purple-600">Time: {verification.layers.forensics.time}s</div>
                      </div>
                      
                      <div className="bg-green-50 p-3 rounded">
                        <div className="font-medium text-green-900">Layer 3: Signatures</div>
                        <div className="text-green-700">Seals: {verification.layers.signatures.seals} | Sigs: {verification.layers.signatures.signatures}</div>
                        <div className="text-green-600">Time: {verification.layers.signatures.time}s</div>
                      </div>
                    </div>
                    
                    <div className="mt-4 flex space-x-2">
                      <button className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
                        View Evidence
                      </button>
                      <button className="text-xs bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-700">
                        Download Report
                      </button>
                      {verification.status === 'requires_review' && (
                        <button className="text-xs bg-yellow-600 text-white px-3 py-1 rounded hover:bg-yellow-700">
                          Review Now
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
