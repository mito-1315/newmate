import React, { useState, useEffect } from 'react';
import { QrCode, Shield, CheckCircle, XCircle, ExternalLink, Download } from 'lucide-react';

const QRViewer = ({ verificationId, attestationId, onClose }) => {
  const [attestation, setAttestation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [verificationResult, setVerificationResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (attestationId) {
      fetchAttestation();
    } else if (verificationId) {
      fetchVerification();
    }
  }, [attestationId, verificationId]);

  const fetchAttestation = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/attestations/${attestationId}`);
      if (!response.ok) {
        throw new Error('Attestation not found');
      }
      const data = await response.json();
      setAttestation(data);
      
      // Also fetch the verification details
      if (data.verification_id) {
        fetchVerificationDetails(data.verification_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchVerification = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/verifications/${verificationId}`);
      if (!response.ok) {
        throw new Error('Verification not found');
      }
      const data = await response.json();
      setVerificationResult(data);
      
      // Check if there's an associated attestation
      if (data.attestation) {
        setAttestation(data.attestation);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchVerificationDetails = async (verId) => {
    try {
      const response = await fetch(`/verifications/${verId}`);
      if (response.ok) {
        const data = await response.json();
        setVerificationResult(data);
      }
    } catch (err) {
      console.error('Failed to fetch verification details:', err);
    }
  };

  const verifySignature = async () => {
    if (!attestation) return;

    try {
      const response = await fetch('/verify-signature', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          attestation_id: attestation.attestation_id,
          signature: attestation.signature,
          public_key: attestation.public_key
        }),
      });

      const result = await response.json();
      alert(result.valid ? 'Signature is valid!' : 'Signature verification failed!');
    } catch (err) {
      alert('Error verifying signature');
    }
  };

  const downloadPDF = async () => {
    if (!attestation?.pdf_url) return;

    try {
      const response = await fetch(attestation.pdf_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `certificate-attestation-${attestation.attestation_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert('Failed to download PDF');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'verified':
        return <CheckCircle className="h-6 w-6 text-green-500" />;
      case 'failed':
        return <XCircle className="h-6 w-6 text-red-500" />;
      default:
        return <Shield className="h-6 w-6 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'verified':
        return 'text-green-800 bg-green-100';
      case 'failed':
        return 'text-red-800 bg-red-100';
      case 'requires_review':
        return 'text-yellow-800 bg-yellow-100';
      default:
        return 'text-gray-800 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading verification details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <XCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
            <h3 className="text-lg font-medium text-red-900 mb-2">Error</h3>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={onClose}
              className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <QrCode className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              Certificate Verification
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <span className="sr-only">Close</span>
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Verification Status */}
          {verificationResult && (
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium text-gray-900">Verification Status</h3>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(verificationResult.status)}
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(verificationResult.status)}`}>
                    {verificationResult.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Risk Level: </span>
                  <span className="font-medium">{verificationResult.risk_score?.risk_level}</span>
                </div>
                <div>
                  <span className="text-gray-500">Confidence: </span>
                  <span className="font-medium">
                    {Math.round((verificationResult.risk_score?.confidence || 0) * 100)}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* QR Code Display */}
          {attestation?.qr_code_url && (
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Verification QR Code</h3>
              <div className="inline-block p-4 bg-white border-2 border-gray-300 rounded-lg">
                <img
                  src={attestation.qr_code_url}
                  alt="Verification QR Code"
                  className="w-48 h-48"
                />
              </div>
              <p className="text-sm text-gray-500 mt-2">
                Scan this QR code to verify the certificate authenticity
              </p>
            </div>
          )}

          {/* Certificate Details */}
          {verificationResult?.extracted_fields && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Certificate Details</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(verificationResult.extracted_fields).map(([key, value]) => {
                    if (!value || key === 'additional_fields') return null;
                    return (
                      <div key={key}>
                        <dt className="text-sm text-gray-500 capitalize">
                          {key.replace('_', ' ')}
                        </dt>
                        <dd className="font-medium text-gray-900">{value}</dd>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Attestation Details */}
          {attestation && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Digital Attestation</h3>
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div>
                  <dt className="text-sm text-gray-500">Attestation ID</dt>
                  <dd className="font-mono text-sm text-gray-900 break-all">
                    {attestation.attestation_id}
                  </dd>
                </div>
                
                <div>
                  <dt className="text-sm text-gray-500">Created</dt>
                  <dd className="text-sm text-gray-900">
                    {new Date(attestation.created_at).toLocaleString()}
                  </dd>
                </div>

                <div>
                  <dt className="text-sm text-gray-500">Digital Signature</dt>
                  <dd className="font-mono text-xs text-gray-600 break-all bg-white p-2 rounded border">
                    {attestation.signature.substring(0, 100)}...
                  </dd>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
            {attestation && (
              <>
                <button
                  onClick={verifySignature}
                  className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  <Shield className="h-4 w-4" />
                  <span>Verify Signature</span>
                </button>

                {attestation.pdf_url && (
                  <button
                    onClick={downloadPDF}
                    className="flex items-center justify-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
                  >
                    <Download className="h-4 w-4" />
                    <span>Download PDF</span>
                  </button>
                )}

                <a
                  href={`/verify/${verificationId || attestation.verification_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center space-x-2 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span>Public View</span>
                </a>
              </>
            )}
          </div>

          {/* Warning for failed verification */}
          {verificationResult?.status === 'failed' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <XCircle className="h-5 w-5 text-red-500 mr-2" />
                <h4 className="text-red-800 font-medium">Verification Failed</h4>
              </div>
              <p className="text-red-700 text-sm mt-1">
                This certificate could not be verified. Please check the certificate authenticity
                through other means or contact the issuing institution.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QRViewer;
