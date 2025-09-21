import React, { useState, useRef, useEffect } from 'react';
import { X, Camera, QrCode, CheckCircle, XCircle } from 'lucide-react';

const QRScannerModal = ({ isOpen, onClose, certificateData }) => {
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    if (isOpen && scanning) {
      startCamera();
    } else {
      stopCamera();
    }

    return () => {
      stopCamera();
    };
  }, [isOpen, scanning]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        } 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
      }
    } catch (err) {
      console.error('Error accessing camera:', err);
      setError('Unable to access camera. Please check permissions.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  const handleScan = () => {
    setScanning(true);
    setError(null);
    setScanResult(null);
  };

  const handleClose = () => {
    setScanning(false);
    setScanResult(null);
    setError(null);
    onClose();
  };

  const simulateQRScan = () => {
    // Simulate QR code scanning for demo purposes
    setScanning(false);
    setScanResult({
      success: true,
      message: 'QR Code scanned successfully!',
      certificateId: certificateData?.certificate_id,
      verificationUrl: certificateData?.verification_url
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center">
            <QrCode className="h-6 w-6 text-blue-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">QR Code Scanner</h3>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {!scanning && !scanResult && (
            <div className="text-center">
              <div className="mb-4">
                <QrCode className="h-16 w-16 text-blue-600 mx-auto mb-4" />
                <h4 className="text-lg font-medium text-gray-900 mb-2">
                  Scan QR Code to Verify
                </h4>
                <p className="text-sm text-gray-600 mb-6">
                  Position the QR code within the camera view to verify the certificate authenticity.
                </p>
              </div>

              {/* Certificate Info */}
              {certificateData && (
                <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
                  <h5 className="font-medium text-gray-900 mb-2">Certificate Details:</h5>
                  <div className="space-y-1 text-sm text-gray-600">
                    <p><strong>Student:</strong> {certificateData.student_name}</p>
                    <p><strong>Course:</strong> {certificateData.course_name}</p>
                    <p><strong>ID:</strong> {certificateData.certificate_id}</p>
                  </div>
                </div>
              )}

              <div className="flex space-x-3">
                <button
                  onClick={handleScan}
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center justify-center"
                >
                  <Camera className="h-4 w-4 mr-2" />
                  Start Scanning
                </button>
                <button
                  onClick={simulateQRScan}
                  className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 flex items-center justify-center"
                >
                  <QrCode className="h-4 w-4 mr-2" />
                  Simulate Scan
                </button>
              </div>
            </div>
          )}

          {scanning && (
            <div className="text-center">
              <div className="mb-4">
                <div className="relative bg-black rounded-lg overflow-hidden mb-4">
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    className="w-full h-64 object-cover"
                  />
                  <div className="absolute inset-0 border-2 border-blue-500 border-dashed rounded-lg m-4">
                    <div className="absolute top-2 left-2 right-2 h-8 bg-blue-500 bg-opacity-20 rounded"></div>
                    <div className="absolute bottom-2 left-2 right-2 h-8 bg-blue-500 bg-opacity-20 rounded"></div>
                    <div className="absolute top-2 left-2 bottom-2 w-8 bg-blue-500 bg-opacity-20 rounded"></div>
                    <div className="absolute top-2 right-2 bottom-2 w-8 bg-blue-500 bg-opacity-20 rounded"></div>
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  Position the QR code within the frame above
                </p>
              </div>

              <button
                onClick={() => setScanning(false)}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
              >
                Stop Scanning
              </button>
            </div>
          )}

          {scanResult && (
            <div className="text-center">
              <div className="mb-4">
                {scanResult.success ? (
                  <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
                ) : (
                  <XCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
                )}
                <h4 className={`text-lg font-medium mb-2 ${
                  scanResult.success ? 'text-green-900' : 'text-red-900'
                }`}>
                  {scanResult.message}
                </h4>
                {scanResult.certificateId && (
                  <p className="text-sm text-gray-600 mb-4">
                    Certificate ID: {scanResult.certificateId}
                  </p>
                )}
              </div>

              <div className="flex space-x-3">
                {scanResult.verificationUrl && (
                  <a
                    href={scanResult.verification_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center justify-center"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    View Certificate
                  </a>
                )}
                <button
                  onClick={handleClose}
                  className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
                >
                  Close
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="text-center">
              <XCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-red-900 mb-2">Error</h4>
              <p className="text-sm text-red-600 mb-4">{error}</p>
              <button
                onClick={handleClose}
                className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QRScannerModal;
