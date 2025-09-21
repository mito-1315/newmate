import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  Download, 
  QrCode, 
  AlertCircle, 
  CheckCircle, 
  Plus, 
  Building, 
  GraduationCap,
  Award,
  Calendar,
  Hash,
  Send,
  Eye,
  ArrowLeft
} from 'lucide-react';

const CertificateIssuance = () => {
  const [activeTab, setActiveTab] = useState('single');
  const [issuanceResult, setIssuanceResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [certificateDetails, setCertificateDetails] = useState(null);
  const [autoFetching, setAutoFetching] = useState(false);

  // Single certificate form
  const [singleCertData, setSingleCertData] = useState({
    student_name: '',
    roll_no: '',
    course_name: '',
    institution_name: '',
    department: '',
    year_of_passing: new Date().getFullYear().toString(),
    grade: '',
    cgpa: '',
    issue_date: new Date().toISOString().split('T')[0],
    additional_fields: {}
  });

  // Certificate image
  const [certificateImage, setCertificateImage] = useState(null);

  // Bulk import
  const [bulkFile, setBulkFile] = useState(null);
  const [bulkResults, setBulkResults] = useState(null);

  // Auto-fetch certificate details
  const fetchCertificateDetails = async (certificateId) => {
    if (!certificateId) return;
    
    setAutoFetching(true);
    try {
      const response = await fetch(`http://localhost:8000/certificate/${certificateId}`);
      if (response.ok) {
        const data = await response.json();
        setCertificateDetails(data);
        console.log('Certificate details fetched:', data);
      } else {
        console.error('Failed to fetch certificate details');
      }
    } catch (error) {
      console.error('Error fetching certificate details:', error);
    } finally {
      setAutoFetching(false);
    }
  };

  // Auto-fetch when issuance result changes
  useEffect(() => {
    if (issuanceResult && issuanceResult.certificate_id) {
      fetchCertificateDetails(issuanceResult.certificate_id);
    }
  }, [issuanceResult]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    console.log(`Form field changed: ${name} = ${value}`);
    setSingleCertData(prev => {
      const newData = {
        ...prev,
        [name]: value
      };
      console.log('Updated form data:', newData);
      return newData;
    });
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setCertificateImage(file);
    }
  };

  const handleSingleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      console.log('Starting certificate issuance...');
      console.log('Certificate data:', singleCertData);
      console.log('Certificate image:', certificateImage);
      
      // Validate required fields before sending
      const requiredFields = ['student_name', 'course_name', 'institution_name'];
      const missingFields = requiredFields.filter(field => !singleCertData[field]);
      
      if (missingFields.length > 0) {
        throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
      }
      
      const formData = new FormData();
      if (certificateImage) {
        formData.append('file', certificateImage);
        console.log('File added to FormData');
      } else {
        console.log('No certificate image provided');
      }
      formData.append('certificate_data', JSON.stringify(singleCertData));
      console.log('Certificate data added to FormData');
      console.log('JSON stringified data:', JSON.stringify(singleCertData));
      
      // Debug: Check what's actually in FormData
      console.log('FormData contents:');
      for (let [key, value] of formData.entries()) {
        console.log(`${key}:`, value);
      }

      console.log('Making request to /issue/certificate...');
      const response = await fetch('/issue/certificate', {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`Issuance failed: ${response.statusText} - ${errorText}`);
      }

      const result = await response.json();
      console.log('Success result:', result);
      setIssuanceResult(result);
    } catch (err) {
      console.error('Certificate issuance error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', bulkFile);

      const response = await fetch('/issue/bulk', {
        method: 'POST',
        body: formData,
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

  const handleDownloadCertificate = () => {
    if (issuanceResult?.pdf_url) {
    const link = document.createElement('a');
      link.href = issuanceResult.pdf_url;
      link.download = `certificate_${singleCertData.roll_no}.pdf`;
    link.click();
    }
  };

  const handleSendToStudent = async () => {
    if (issuanceResult?.id) {
      try {
        const response = await fetch('/issue/send-email', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            certificate_id: issuanceResult.id,
            student_email: singleCertData.email,
          }),
        });

        if (response.ok) {
          alert('Certificate sent to student email successfully!');
        } else {
          throw new Error('Failed to send email');
        }
      } catch (error) {
        console.error('Error sending email:', error);
        alert('Failed to send email. Please try again.');
      }
    }
  };

  const tabs = [
    { id: 'single', name: 'Single Certificate', icon: Plus },
    { id: 'bulk', name: 'Bulk Upload', icon: Upload },
    { id: 'preview', name: 'Certificate Preview', icon: Eye },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => window.history.back()}
                className="mr-4 p-2 text-gray-400 hover:text-gray-600"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <Building className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">
                Certificate Issuance
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">University Admin</span>
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
            {activeTab === 'single' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Issue Single Certificate</h3>
              <p className="mt-1 text-sm text-gray-500">
                Enter student details to generate a digital certificate with QR code
              </p>
            </div>
            <form onSubmit={handleSingleSubmit} className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Student Name *
                      </label>
                      <input
                        type="text"
                    name="student_name"
                    value={singleCertData.student_name}
                    onChange={handleInputChange}
                        required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter student's full name"
                      />
                    </div>

                    <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Roll No / Registration ID *
                      </label>
                      <input
                        type="text"
                    name="roll_no"
                    value={singleCertData.roll_no}
                    onChange={handleInputChange}
                        required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter roll number"
                      />
                    </div>

                    <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Course Name *
                      </label>
                      <input
                        type="text"
                    name="course_name"
                    value={singleCertData.course_name}
                    onChange={handleInputChange}
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter course name"
                      />
                    </div>

                    <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Year of Passing *
                      </label>
                      <input
                    type="number"
                    name="year_of_passing"
                    value={singleCertData.year_of_passing}
                    onChange={handleInputChange}
                        required
                    min="1900"
                    max="2030"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter year"
                      />
                    </div>

                    <div>
                  <label className="block text-sm font-medium text-gray-700">
                        Institution *
                      </label>
                      <input
                        type="text"
                    name="institution_name"
                    value={singleCertData.institution_name}
                    onChange={handleInputChange}
                        required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter institution name"
                      />
                    </div>

                    <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Department
                      </label>
                      <input
                    type="text"
                    name="department"
                    value={singleCertData.department}
                    onChange={handleInputChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter department"
                      />
                    </div>

                    <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Grade / CGPA
                      </label>
                      <input
                        type="text"
                    name="grade"
                    value={singleCertData.grade}
                    onChange={handleInputChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter grade or CGPA"
                      />
                    </div>

                    <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Issue Date
                  </label>
                  <input
                    type="date"
                    name="issue_date"
                    value={singleCertData.issue_date}
                    onChange={handleInputChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Certificate Image (Optional)
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600">
                      <label className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                        <span>Upload certificate image</span>
                        <input
                          type="file"
                          accept="image/*,.pdf"
                          onChange={handleImageUpload}
                          className="sr-only"
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-gray-500">PNG, JPG, PDF up to 10MB</p>
                  </div>
                </div>
                {certificateImage && (
                  <p className="mt-2 text-sm text-green-600">
                    ✓ {certificateImage.name} selected
                  </p>
                )}
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
                  {error}
                </div>
              )}

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    console.log('Current form data:', singleCertData);
                    console.log('Required fields check:');
                    console.log('student_name:', singleCertData.student_name);
                    console.log('course_name:', singleCertData.course_name);
                    console.log('institution_name:', singleCertData.institution_name);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Debug Form Data
                </button>
                <button
                  type="button"
                  onClick={() => window.history.back()}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Cancel
                </button>
                  <button
                    type="submit"
                    disabled={loading}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                  {loading ? 'Generating...' : 'Generate Certificate'}
                  </button>
              </div>
            </form>
              </div>
            )}

            {activeTab === 'bulk' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Bulk Certificate Upload</h3>
              <p className="mt-1 text-sm text-gray-500">
                Upload certificates from ERP system or CSV file
              </p>
            </div>
            <form onSubmit={handleBulkSubmit} className="p-6">
              <div className="space-y-6">
              <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Upload CSV/Excel File
                    </label>
                  <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                    <div className="space-y-1 text-center">
                      <Upload className="mx-auto h-12 w-12 text-gray-400" />
                      <div className="flex text-sm text-gray-600">
                        <label className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                          <span>Upload file</span>
                    <input
                      type="file"
                            accept=".csv,.xlsx,.xls"
                      onChange={(e) => setBulkFile(e.target.files[0])}
                            className="sr-only"
                            required
                          />
                        </label>
                        <p className="pl-1">or drag and drop</p>
                      </div>
                      <p className="text-xs text-gray-500">CSV, XLSX, XLS up to 50MB</p>
                    </div>
                  </div>
                  {bulkFile && (
                    <p className="mt-2 text-sm text-green-600">
                      ✓ {bulkFile.name} selected
                    </p>
                  )}
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <h4 className="text-sm font-medium text-blue-800 mb-2">CSV Format Requirements:</h4>
                  <ul className="text-sm text-blue-700 list-disc list-inside space-y-1">
                    <li>student_name, roll_no, course_name, year_of_passing, institution, department, grade</li>
                    <li>First row should contain column headers</li>
                    <li>Maximum 1000 certificates per upload</li>
                  </ul>
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
                    {error}
                  </div>
                )}

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => window.history.back()}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading || !bulkFile}
                    className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {loading ? 'Processing...' : 'Upload & Process'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        )}

        {activeTab === 'preview' && issuanceResult && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Certificate Preview</h3>
              <p className="mt-1 text-sm text-gray-500">
                Review the generated certificate before finalizing
                {autoFetching && <span className="ml-2 text-blue-600">🔄 Auto-fetching details...</span>}
              </p>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* QR Code Certificate */}
              <div>
                  <h4 className="text-md font-medium text-gray-900 mb-4">QR Certificate</h4>
                  <div className="border border-gray-200 rounded-lg p-4 text-center">
                    <img
                      src={issuanceResult.certificate_image_url || issuanceResult.image_url}
                      alt="QR Certificate"
                      className="max-w-md mx-auto h-auto rounded"
                    />
                    <p className="mt-2 text-sm text-gray-600">
                      Scan QR code to verify certificate authenticity
                    </p>
                  </div>
                </div>

                {/* Certificate Details */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-4">Certificate Details</h4>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Student Name:</span>
                      <span className="text-sm font-medium">
                        {certificateDetails?.student_name || singleCertData.student_name}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Roll No:</span>
                      <span className="text-sm font-medium">
                        {certificateDetails?.roll_number || singleCertData.roll_no}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Course:</span>
                      <span className="text-sm font-medium">
                        {certificateDetails?.course_name || singleCertData.course_name}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Institution:</span>
                      <span className="text-sm font-medium">
                        {certificateDetails?.institution || singleCertData.institution_name}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Year:</span>
                      <span className="text-sm font-medium">
                        {certificateDetails?.year || singleCertData.year_of_passing}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Grade:</span>
                      <span className="text-sm font-medium">
                        {certificateDetails?.grade || singleCertData.grade}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Certificate ID:</span>
                      <span className="text-sm font-medium font-mono">
                        {certificateDetails?.certificate_id || issuanceResult.certificate_id}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Status:</span>
                      <span className="text-sm font-medium text-green-600">
                        <CheckCircle className="h-4 w-4 inline mr-1" />
                        Generated
                      </span>
                    </div>
                  </div>

                  {/* QR Code */}
                  <div className="mt-4">
                    <h5 className="text-sm font-medium text-gray-900 mb-2">Verification</h5>
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <p className="text-sm text-gray-600 mb-2">
                        Verification URL:
                      </p>
                      <p className="text-xs font-mono bg-gray-100 p-2 rounded break-all">
                        {certificateDetails?.verification_url || issuanceResult.verification_url || 'Not available'}
                      </p>
                      <p className="text-xs text-gray-500 mt-2">
                        Scan QR code above or visit URL to verify
                      </p>
                      {certificateDetails?.verification_url && (
                        <div className="mt-2">
                          <a 
                            href={certificateDetails.verification_url}
                    target="_blank"
                    rel="noopener noreferrer"
                            className="inline-flex items-center text-xs text-blue-600 hover:text-blue-800"
                          >
                            <Eye className="h-3 w-3 mr-1" />
                            Open Verification Page
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-6 flex justify-between">
                <button
                  onClick={() => setActiveTab('single')}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Issue Another Certificate
                </button>
                <div className="space-x-3">
                  <button
                    onClick={handleDownloadCertificate}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download PDF
                  </button>
                  <button
                    onClick={handleSendToStudent}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <Send className="h-4 w-4 mr-2" />
                    Send to Student
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'preview' && !issuanceResult && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Certificate Preview</h3>
              </div>
            <div className="p-6">
              <div className="text-center py-12">
                <Eye className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No certificate generated</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Generate a certificate first to see the preview
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CertificateIssuance;