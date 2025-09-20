import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { CheckCircle, XCircle, AlertTriangle, Shield, QrCode, Download, ExternalLink, FileText, Calendar, Award, Building, User, Hash, Clock } from 'lucide-react';

const PublicVerification = () => {
  const { attestationId } = useParams();
  const [verificationResult, setVerificationResult] = useState(null);
  const [certificateImage, setCertificateImage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (attestationId) {
      verifyByAttestationId(attestationId);
    }
  }, [attestationId]);

  const verifyByAttestationId = async (id) => {
    setLoading(true);
    setError(null);

    try {
      // Verify certificate
      const verifyResponse = await fetch(`/verify/${id}`);
      if (!verifyResponse.ok) {
        throw new Error(`Verification failed: ${verifyResponse.statusText}`);
      }
      const verifyData = await verifyResponse.json();
      setVerificationResult(verifyData);

      // Get certificate image if verification is successful
      if (verifyData.valid) {
        try {
          const imageResponse = await fetch(`/verify/${id}/image`);
          if (imageResponse.ok) {
            const imageData = await imageResponse.json();
            setCertificateImage(imageData);
          }
        } catch (imgError) {
          console.warn('Certificate image not available:', imgError);
        }
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (valid) => {
    if (valid) {
      return <CheckCircle className="h-12 w-12 text-green-500" />;
    } else {
      return <XCircle className="h-12 w-12 text-red-500" />;
    }
  };

  const getStatusColor = (valid) => {
    return valid ? 'text-green-800 bg-green-100' : 'text-red-800 bg-red-100';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Verifying certificate...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full mx-4 bg-white rounded-lg shadow-md p-6 text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-red-900 mb-2">Verification Error</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => window.history.back()}
            className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Shield className="h-8 w-8 text-blue-600 mr-2" />
            <h1 className="text-3xl font-bold text-gray-900">
              Certificate Verification
            </h1>
          </div>
          <p className="text-gray-600">
            Digital certificate authenticity verification
          </p>
        </div>

        {/* Verification Status */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="text-center mb-6">
            {getStatusIcon(verificationResult?.valid)}
            <h2 className="text-2xl font-bold mt-4">
              {verificationResult?.valid ? 'Certificate Verified' : 'Verification Failed'}
            </h2>
            <p className={`inline-flex px-4 py-2 rounded-full text-sm font-medium mt-2 ${getStatusColor(verificationResult?.valid)}`}>
              {verificationResult?.valid ? 'AUTHENTIC' : 'INVALID'}
            </p>
          </div>

          {!verificationResult?.valid && verificationResult?.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
                <span className="text-red-700 font-medium">Error: </span>
                <span className="text-red-600">{verificationResult.error}</span>
              </div>
            </div>
          )}
        </div>

        {/* Certificate Details */}
        {verificationResult?.valid && verificationResult?.certificate_details && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-6 flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              Certificate Information
            </h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Student Information */}
              <div className="space-y-6">
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
                    <User className="h-4 w-4 mr-2" />
                    Student Information
                  </h4>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Full Name:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {verificationResult.certificate_details.student_name || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Roll Number:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {verificationResult.certificate_details.roll_no || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Certificate ID:</span>
                      <span className="text-sm font-medium text-gray-900 font-mono">
                        {verificationResult.certificate_details.certificate_id || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Course Information */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
                    <Award className="h-4 w-4 mr-2" />
                    Course Details
                  </h4>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Course Name:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {verificationResult.certificate_details.course_name || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Year of Passing:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {verificationResult.certificate_details.year_of_passing || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Grade/CGPA:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {verificationResult.certificate_details.grade || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Institution & Verification Info */}
              <div className="space-y-6">
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
                    <Building className="h-4 w-4 mr-2" />
                    Institution Details
                  </h4>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Institution:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {verificationResult.certificate_details.institution || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Department:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {verificationResult.certificate_details.department || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Issued Date:</span>
                      <span className="text-sm font-medium text-gray-900">
                        {verificationResult.certificate_details.issue_date || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Verification Status */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
                    <Shield className="h-4 w-4 mr-2" />
                    Verification Status
                  </h4>
                  <div className="bg-green-50 rounded-lg p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Status:</span>
                      <span className="text-sm font-medium text-green-800 flex items-center">
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Verified
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Confidence:</span>
                      <span className="text-sm font-medium text-green-800">
                        {Math.round((verificationResult.confidence || 0) * 100)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Verification Time:</span>
                      <span className="text-sm font-medium text-green-800">
                        {new Date().toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Certificate Image */}
        {certificateImage && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <QrCode className="h-5 w-5 mr-2" />
              Certificate Image
            </h3>
            
            <div className="text-center">
              <img
                src={certificateImage.image_url}
                alt="Certificate"
                className="max-w-full h-auto border border-gray-200 rounded-lg shadow-sm"
              />
              
              <div className="mt-4 flex justify-center space-x-4">
                <a
                  href={certificateImage.image_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Full Size
                </a>
                
                <a
                  href={certificateImage.image_url}
                  download
                  className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </a>
              </div>
            </div>
          </div>
        )}

        {/* Verification Details */}
        {verificationResult?.valid && verificationResult?.verification_details && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Shield className="h-5 w-5 mr-2" />
              Verification Details
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-700 mb-3">Security Checks</h4>
                <div className="space-y-2">
                  <div className="flex items-center">
                    {verificationResult.verification_details.signature_valid ? (
                      <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500 mr-2" />
                    )}
                    <span className="text-sm">Digital Signature</span>
                  </div>
                  
                  {verificationResult.verification_details.image_integrity?.available && (
                    <div className="flex items-center">
                      {verificationResult.verification_details.image_integrity.integrity_verified ? (
                        <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500 mr-2" />
                      )}
                      <span className="text-sm">Image Integrity</span>
                    </div>
                  )}
                  
                  <div className="flex items-center">
                    {verificationResult.verification_details.certificate_status?.valid ? (
                      <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500 mr-2" />
                    )}
                    <span className="text-sm">Certificate Status</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-700 mb-3">Issuer Information</h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-500">Institution:</span>
                    <span className="ml-2 font-medium">{verificationResult.issuer_information?.institution}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Public Key Verified:</span>
                    <span className="ml-2">
                      {verificationResult.issuer_information?.public_key_verified ? (
                        <span className="text-green-600 font-medium">Yes</span>
                      ) : (
                        <span className="text-red-600 font-medium">No</span>
                      )}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Verified At:</span>
                    <span className="ml-2 font-medium">
                      {new Date(verificationResult.verification_details.verified_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* QR Verification Information */}
        {verificationResult?.qr_verification && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <QrCode className="h-5 w-5 mr-2" />
              QR Code Verification
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">QR Detected:</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  verificationResult.qr_verification.qr_detected 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {verificationResult.qr_verification.qr_detected ? 'Yes' : 'No'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">QR Signature Valid:</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  verificationResult.qr_verification.signature_valid 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {verificationResult.qr_verification.signature_valid ? 'Valid' : 'Invalid'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Issuer Verified:</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  verificationResult.qr_verification.issuer_verified 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {verificationResult.qr_verification.issuer_verified ? 'Verified' : 'Not Verified'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Field Consistency Check */}
        {verificationResult?.field_consistency && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Field Consistency Check
            </h3>
            
            <div className="mb-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Overall Match:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  verificationResult.field_consistency.all_match 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {verificationResult.field_consistency.match_percentage}% Match
                </span>
              </div>
            </div>

            {verificationResult.field_consistency.discrepancies?.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-medium text-yellow-800 mb-2">Discrepancies Found:</h4>
                <ul className="list-disc list-inside text-sm text-yellow-700">
                  {verificationResult.field_consistency.discrepancies.map((discrepancy, index) => (
                    <li key={index}>{discrepancy}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          <p>
            This verification was performed using cryptographic signatures and blockchain technology.
          </p>
          <p className="mt-1">
            Verification ID: {attestationId}
          </p>
        </div>
      </div>
    </div>
  );
};

export default PublicVerification;
