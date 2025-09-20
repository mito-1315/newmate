import React, { useState } from 'react';
import { Upload, FileText, Download, QrCode, AlertCircle, CheckCircle } from 'lucide-react';

const CertificateIssuance = () => {
  const [activeTab, setActiveTab] = useState('single');
  const [issuanceResult, setIssuanceResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Single certificate form
  const [singleCertData, setSingleCertData] = useState({
    certificate_id: '',
    student_name: '',
    roll_no: '',
    course_name: '',
    institution: '',
    issue_date: new Date().toISOString().split('T')[0],
    year: new Date().getFullYear().toString(),
    grade: ''
  });

  // Bulk import
  const [bulkFile, setBulkFile] = useState(null);
  const [bulkResults, setBulkResults] = useState(null);

  const handleSingleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/issue/certificate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          certificate_data: singleCertData,
          institution_id: 'default'
        }),
      });

      if (!response.ok) {
        throw new Error(`Issuance failed: ${response.statusText}`);
      }

      const result = await response.json();
      setIssuanceResult(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkUpload = async (file) => {
    setLoading(true);
    setError(null);

    try {
      // Parse CSV file (simplified - in production use proper CSV parser)
      const text = await file.text();
      const lines = text.split('\n');
      const headers = lines[0].split(',').map(h => h.trim());
      
      const certificates = lines.slice(1).filter(line => line.trim()).map(line => {
        const values = line.split(',').map(v => v.trim());
        const cert = {};
        headers.forEach((header, index) => {
          cert[header] = values[index] || '';
        });
        return cert;
      });

      const response = await fetch('/api/issue/bulk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          certificates_data: { certificates },
          institution_id: 'default'
        }),
      });

      if (!response.ok) {
        throw new Error(`Bulk issuance failed: ${response.statusText}`);
      }

      const result = await response.json();
      setBulkResults(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadQRCode = (qrDataUrl, certificateId) => {
    const link = document.createElement('a');
    link.href = qrDataUrl;
    link.download = `qr_${certificateId}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Certificate Issuance System
          </h1>
          <p className="text-gray-600">
            Issue certificates with QR codes and digital attestation
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex">
              <button
                onClick={() => setActiveTab('single')}
                className={`w-1/2 py-4 px-6 text-center font-medium ${
                  activeTab === 'single'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <FileText className="h-5 w-5 inline mr-2" />
                Single Certificate
              </button>
              <button
                onClick={() => setActiveTab('bulk')}
                className={`w-1/2 py-4 px-6 text-center font-medium ${
                  activeTab === 'bulk'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Upload className="h-5 w-5 inline mr-2" />
                Bulk Import
              </button>
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'single' && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Issue Single Certificate
                </h3>
                
                <form onSubmit={handleSingleSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Certificate ID *
                      </label>
                      <input
                        type="text"
                        required
                        value={singleCertData.certificate_id}
                        onChange={(e) => setSingleCertData({...singleCertData, certificate_id: e.target.value})}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="CS2023-001234"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Student Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={singleCertData.student_name}
                        onChange={(e) => setSingleCertData({...singleCertData, student_name: e.target.value})}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="John Doe"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Roll Number
                      </label>
                      <input
                        type="text"
                        value={singleCertData.roll_no}
                        onChange={(e) => setSingleCertData({...singleCertData, roll_no: e.target.value})}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="2021CS001"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Course Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={singleCertData.course_name}
                        onChange={(e) => setSingleCertData({...singleCertData, course_name: e.target.value})}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Computer Science"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Institution *
                      </label>
                      <input
                        type="text"
                        required
                        value={singleCertData.institution}
                        onChange={(e) => setSingleCertData({...singleCertData, institution: e.target.value})}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="University of Technology"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Issue Date
                      </label>
                      <input
                        type="date"
                        value={singleCertData.issue_date}
                        onChange={(e) => setSingleCertData({...singleCertData, issue_date: e.target.value})}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Year
                      </label>
                      <input
                        type="text"
                        value={singleCertData.year}
                        onChange={(e) => setSingleCertData({...singleCertData, year: e.target.value})}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="2023"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Grade
                      </label>
                      <input
                        type="text"
                        value={singleCertData.grade}
                        onChange={(e) => setSingleCertData({...singleCertData, grade: e.target.value})}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="First Class Honours"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {loading ? 'Issuing Certificate...' : 'Issue Certificate'}
                  </button>
                </form>
              </div>
            )}

            {activeTab === 'bulk' && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Bulk Certificate Import
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Upload CSV File
                    </label>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={(e) => setBulkFile(e.target.files[0])}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      CSV should include: certificate_id, student_name, course_name, institution, issue_date, year, grade
                    </p>
                  </div>

                  <button
                    onClick={() => bulkFile && handleBulkUpload(bulkFile)}
                    disabled={!bulkFile || loading}
                    className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
                  >
                    {loading ? 'Processing...' : 'Process Bulk Import'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
              <span className="text-red-700">{error}</span>
            </div>
          </div>
        )}

        {/* Single Certificate Result */}
        {issuanceResult && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center mb-4">
              <CheckCircle className="h-6 w-6 text-green-500 mr-2" />
              <h3 className="text-lg font-medium text-gray-900">
                Certificate Issued Successfully
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Certificate Details</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="text-gray-500">ID:</span> {issuanceResult.certificate_id}</div>
                  <div><span className="text-gray-500">Issuance ID:</span> {issuanceResult.issuance_id}</div>
                  <div><span className="text-gray-500">Status:</span> {issuanceResult.status}</div>
                  <div><span className="text-gray-500">Issued:</span> {new Date(issuanceResult.issued_at).toLocaleString()}</div>
                </div>

                <div className="mt-4 space-y-2">
                  <a
                    href={issuanceResult.certificate_image_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download Certificate
                  </a>
                  
                  <button
                    onClick={() => downloadQRCode(issuanceResult.qr_code_data, issuanceResult.certificate_id)}
                    className="inline-flex items-center px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm ml-2"
                  >
                    <QrCode className="h-4 w-4 mr-2" />
                    Download QR Code
                  </button>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">QR Code Preview</h4>
                {issuanceResult.qr_code_data && (
                  <img
                    src={issuanceResult.qr_code_data}
                    alt="Certificate QR Code"
                    className="w-32 h-32 border border-gray-200 rounded"
                  />
                )}
                
                <div className="mt-2">
                  <p className="text-sm text-gray-600">Verification URL:</p>
                  <a
                    href={issuanceResult.verification_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:text-blue-700 break-all"
                  >
                    {issuanceResult.verification_url}
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Bulk Results */}
        {bulkResults && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Bulk Import Results
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{bulkResults.total}</div>
                <div className="text-sm text-blue-600">Total Processed</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{bulkResults.successful.length}</div>
                <div className="text-sm text-green-600">Successful</div>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{bulkResults.failed.length}</div>
                <div className="text-sm text-red-600">Failed</div>
              </div>
            </div>

            {bulkResults.successful.length > 0 && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-2">Successful Certificates</h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Row</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Certificate ID</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Verification URL</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {bulkResults.successful.map((cert, index) => (
                        <tr key={index}>
                          <td className="px-4 py-2 text-sm text-gray-900">{cert.row}</td>
                          <td className="px-4 py-2 text-sm text-gray-900">{cert.certificate_id}</td>
                          <td className="px-4 py-2 text-sm">
                            <a
                              href={cert.verification_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-700"
                            >
                              Verify
                            </a>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {bulkResults.failed.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Failed Certificates</h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Row</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Certificate ID</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Error</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {bulkResults.failed.map((cert, index) => (
                        <tr key={index}>
                          <td className="px-4 py-2 text-sm text-gray-900">{cert.row}</td>
                          <td className="px-4 py-2 text-sm text-gray-900">{cert.certificate_id}</td>
                          <td className="px-4 py-2 text-sm text-red-600">{cert.error}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CertificateIssuance;
