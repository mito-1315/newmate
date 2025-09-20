import React, { useState, useEffect } from 'react';
import { FileText, Download, Eye, QrCode, Mail, Calendar, Award } from 'lucide-react';

const StudentPortal = () => {
  const [certificates, setCertificates] = useState([]);
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudentCertificates();
  }, []);

  const fetchStudentCertificates = async () => {
    try {
      const response = await fetch('/student/certificates');
      if (response.ok) {
        const data = await response.json();
        setCertificates(data.certificates || []);
      }
    } catch (error) {
      console.error('Error fetching certificates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadCertificate = (certificate) => {
    const link = document.createElement('a');
    link.href = certificate.pdf_url;
    link.download = `certificate_${certificate.roll_no}.pdf`;
    link.click();
  };

  const handleViewCertificate = (certificate) => {
    setSelectedCertificate(certificate);
  };

  const handleRequestLegacyVerification = () => {
    // Navigate to legacy verification request page
    window.location.href = '/legacy-verification';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your certificates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Award className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">
                My Certificates
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleRequestLegacyVerification}
                className="px-4 py-2 border border-blue-600 text-blue-600 rounded-md hover:bg-blue-50 text-sm font-medium"
              >
                Request Legacy Verification
              </button>
              <span className="text-sm text-gray-500">Welcome, Student</span>
              <button className="text-sm text-blue-600 hover:text-blue-500">
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {certificates.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No certificates found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Your issued certificates will appear here
            </p>
            <div className="mt-6">
              <button
                onClick={handleRequestLegacyVerification}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Request Legacy Verification
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {certificates.map((certificate) => (
              <div
                key={certificate.id}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <FileText className="h-8 w-8 text-blue-600" />
                      <div className="ml-3">
                        <h3 className="text-lg font-medium text-gray-900">
                          {certificate.course_name}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {certificate.institution_name}
                        </p>
                      </div>
                    </div>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Verified
                    </span>
                  </div>

                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-2" />
                      <span>Year: {certificate.year_of_passing}</span>
                    </div>
                    <div className="flex items-center">
                      <Award className="h-4 w-4 mr-2" />
                      <span>Grade: {certificate.grade || 'N/A'}</span>
                    </div>
                    <div className="flex items-center">
                      <QrCode className="h-4 w-4 mr-2" />
                      <span className="font-mono text-xs">
                        ID: {certificate.id.substring(0, 12)}...
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 flex space-x-2">
                    <button
                      onClick={() => handleViewCertificate(certificate)}
                      className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View
                    </button>
                    <button
                      onClick={() => handleDownloadCertificate(certificate)}
                      className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Certificate Detail Modal */}
      {selectedCertificate && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Certificate Details
              </h3>
              <button
                onClick={() => setSelectedCertificate(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Certificate Image */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-2">Certificate</h4>
                <div className="border border-gray-200 rounded-lg p-4">
                  <img
                    src={selectedCertificate.image_url}
                    alt="Certificate"
                    className="w-full h-auto rounded"
                  />
                </div>
              </div>

              {/* Certificate Details */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-4">Details</h4>
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Student Name:</span>
                    <span className="text-sm font-medium">{selectedCertificate.student_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Roll No:</span>
                    <span className="text-sm font-medium">{selectedCertificate.roll_no}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Course:</span>
                    <span className="text-sm font-medium">{selectedCertificate.course_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Year:</span>
                    <span className="text-sm font-medium">{selectedCertificate.year_of_passing}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Grade:</span>
                    <span className="text-sm font-medium">{selectedCertificate.grade || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Certificate ID:</span>
                    <span className="text-sm font-medium font-mono">{selectedCertificate.id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Status:</span>
                    <span className="text-sm font-medium text-green-600">Verified</span>
                  </div>
                </div>

                {/* QR Code */}
                <div className="mt-4">
                  <h5 className="text-sm font-medium text-gray-900 mb-2">QR Code</h5>
                  <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
                    <img
                      src={selectedCertificate.qr_code_url}
                      alt="QR Code"
                      className="w-24 h-24 mx-auto"
                    />
                    <p className="text-xs text-gray-500 mt-2">
                      Share this QR code for verification
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setSelectedCertificate(null)}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Close
              </button>
              <button
                onClick={() => handleDownloadCertificate(selectedCertificate)}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Download className="h-4 w-4 mr-2" />
                Download PDF
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentPortal;
