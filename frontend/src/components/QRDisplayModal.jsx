import React, { useState, useEffect } from 'react';
import { X, QrCode, Copy, CheckCircle } from 'lucide-react';

const QRDisplayModal = ({ isOpen, onClose, certificateData }) => {
  const [copied, setCopied] = useState(false);

  // Handle escape key to close modal
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  const handleCopyVerificationUrl = () => {
    if (certificateData?.verification_url) {
      navigator.clipboard.writeText(certificateData.verification_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isOpen || !certificateData) return null;

  const handleBackdropClick = (event) => {
    console.log('Backdrop click event:', event.target, event.currentTarget);
    if (event.target === event.currentTarget) {
      console.log('Backdrop clicked, closing modal');
      onClose();
    }
  };

  const handleCloseClick = (event) => {
    console.log('Close button clicked');
    event.stopPropagation();
    onClose();
  };

  const handleModalClick = (event) => {
    event.stopPropagation();
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div 
        className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 relative"
        onClick={handleModalClick}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center">
            <QrCode className="h-6 w-6 text-blue-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">QR Code for Verification</h3>
          </div>
          <button
            onClick={handleCloseClick}
            className="text-gray-400 hover:text-gray-600 transition-colors duration-200 p-1 rounded-full hover:bg-gray-100"
            title="Close"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 text-center">
          {/* Large QR Code */}
          <div className="mb-6">
            <img
              src={certificateData.certificate_image_url || certificateData.qr_code_data}
              alt="QR Code for Verification"
              className="w-80 h-80 mx-auto border border-gray-300 rounded-lg shadow-sm"
            />
          </div>

          {/* Certificate Info */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
            <h4 className="font-medium text-gray-900 mb-3">Certificate Details:</h4>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex justify-between">
                <span className="font-medium">Student:</span>
                <span>{certificateData.student_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Course:</span>
                <span className="text-right">{certificateData.course_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Certificate ID:</span>
                <span className="font-mono text-xs">{certificateData.certificate_id}</span>
              </div>
              {certificateData.verification_url && (
                <div className="pt-2 border-t border-gray-200">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Verification URL:</span>
                    <button
                      onClick={handleCopyVerificationUrl}
                      className="flex items-center text-blue-600 hover:text-blue-800 text-xs"
                    >
                      {copied ? (
                        <>
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3 mr-1" />
                          Copy
                        </>
                      )}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 font-mono break-all mt-1">
                    {certificateData.verification_url}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h5 className="font-medium text-blue-900 mb-2">How to Verify:</h5>
            <ol className="text-sm text-blue-800 text-left space-y-1">
              <li>1. Use any QR code scanner app on your phone</li>
              <li>2. Point your camera at the QR code above</li>
              <li>3. The scanner will open the verification page</li>
              <li>4. View the complete certificate details</li>
            </ol>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3">
            {certificateData.verification_url && (
              <a
                href={certificateData.verification_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center justify-center transition-colors duration-200"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Open Verification Page
              </a>
            )}
            <button
              onClick={handleCloseClick}
              className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors duration-200 flex items-center justify-center"
            >
              <X className="h-4 w-4 mr-2" />
              Close
            </button>
          </div>

          {/* Close Instructions */}
          <div className="mt-4 text-xs text-gray-500 text-center">
            Press <kbd className="px-1 py-0.5 bg-gray-100 rounded text-xs">ESC</kbd> or click outside to close
          </div>
        </div>
      </div>
    </div>
  );
};

export default QRDisplayModal;
