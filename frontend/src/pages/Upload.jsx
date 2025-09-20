import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload as UploadIcon, FileText, AlertCircle, CheckCircle } from 'lucide-react';

const Upload = () => {
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, success, error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploadStatus('uploading');
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
      setUploadStatus('success');
    } catch (err) {
      setError(err.message);
      setUploadStatus('error');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.pdf']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const resetUpload = () => {
    setUploadStatus('idle');
    setResult(null);
    setError(null);
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'verified': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed': return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'requires_review': return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      default: return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Certificate Verification
          </h1>
          <p className="text-gray-600">
            Upload your certificate image for AI-powered verification
          </p>
        </div>

        {uploadStatus === 'idle' && (
          <div className="bg-white rounded-lg shadow-md p-8">
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-blue-400 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...getInputProps()} />
              <UploadIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              {isDragActive ? (
                <p className="text-blue-600 text-lg font-medium">
                  Drop the certificate here...
                </p>
              ) : (
                <div>
                  <p className="text-gray-900 text-lg font-medium mb-2">
                    Drag & drop your certificate here
                  </p>
                  <p className="text-gray-500 mb-4">
                    or click to select a file
                  </p>
                  <p className="text-sm text-gray-400">
                    Supports JPEG, PNG, PDF up to 10MB
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {uploadStatus === 'uploading' && (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Processing your certificate...</p>
          </div>
        )}

        {uploadStatus === 'error' && (
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="text-center mb-6">
              <AlertCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
              <h3 className="text-lg font-medium text-red-900 mb-2">
                Upload Failed
              </h3>
              <p className="text-red-600">{error}</p>
            </div>
            <button
              onClick={resetUpload}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {uploadStatus === 'success' && result && (
          <div className="space-y-6">
            {/* Status Overview */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Verification Result
                </h3>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(result.status)}
                  <span className="font-medium capitalize">
                    {result.status.replace('_', ' ')}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Risk Level</p>
                  <span className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${getRiskLevelColor(result.risk_score.risk_level)}`}>
                    {result.risk_score.risk_level.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">Confidence Score</p>
                  <p className="text-lg font-medium">
                    {Math.round(result.risk_score.confidence * 100)}%
                  </p>
                </div>
              </div>

              {result.risk_score.factors.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm text-gray-500 mb-2">Risk Factors:</p>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {result.risk_score.factors.map((factor, index) => (
                      <li key={index} className="flex items-center space-x-2">
                        <span className="w-1 h-1 bg-gray-400 rounded-full"></span>
                        <span>{factor}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Extracted Fields */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Extracted Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(result.extracted_fields).map(([key, value]) => {
                  if (!value || key === 'additional_fields') return null;
                  return (
                    <div key={key}>
                      <p className="text-sm text-gray-500 mb-1 capitalize">
                        {key.replace('_', ' ')}
                      </p>
                      <p className="font-medium">{value}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* QR Code and Attestation */}
            {result.attestation && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Digital Attestation
                </h3>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Attestation ID</p>
                    <p className="font-mono text-sm">{result.attestation.attestation_id}</p>
                  </div>
                  {result.attestation.qr_code_url && (
                    <img
                      src={result.attestation.qr_code_url}
                      alt="Verification QR Code"
                      className="w-24 h-24"
                    />
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-4">
              <button
                onClick={resetUpload}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
              >
                Verify Another Certificate
              </button>
              {result.requires_manual_review && (
                <button className="flex-1 bg-yellow-600 text-white py-2 px-4 rounded-md hover:bg-yellow-700 transition-colors">
                  Request Manual Review
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Upload;
