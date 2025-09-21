import React, { useState } from 'react';
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
      
      // Always add a file - either the uploaded one or a placeholder
      if (certificateImage) {
        formData.append('file', certificateImage);
        console.log('File added to FormData:', certificateImage.name);
      } else {
        // Create a minimal placeholder file
        const placeholderBlob = new Blob(['placeholder'], { type: 'text/plain' });
        const placeholderFile = new File([placeholderBlob], 'placeholder.txt', { type: 'text/plain' });
        formData.append('file', placeholderFile);
        console.log('Placeholder file added to FormData');
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
      setActiveTab('preview');
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
      console.log('Starting bulk certificate issuance...');
      console.log('Bulk file:', bulkFile);
      
      if (!bulkFile) {
        throw new Error('Please select a CSV file to upload');
      }

      const formData = new FormData();
      formData.append('file', bulkFile);
      formData.append('institution_id', 'default');

      console.log('Making request to /issue/bulk...');
      const response = await fetch('/issue/bulk', {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`Bulk issuance failed: ${response.statusText} - ${errorText}`);
      }

      const result = await response.json();
      console.log('Bulk success result:', result);
      setBulkResults(result);
      
      // Show appropriate success message based on results
      const successCount = result.successful?.length || 0;
      const failedCount = result.failed?.length || 0;
      
      if (successCount > 0 && failedCount === 0) {
        alert(`🎉 Bulk processing completed successfully! All ${successCount} certificates were processed.${successCount > 0 ? '\n\n📝 Note: Running in development mode with mock certificates.' : ''}`);
      } else if (successCount > 0 && failedCount > 0) {
        alert(`⚠️ Bulk processing completed with mixed results!\n✅ ${successCount} certificates processed successfully\n❌ ${failedCount} certificates failed`);
      } else if (failedCount > 0) {
        alert(`❌ Bulk processing failed! ${failedCount} certificates could not be processed.`);
      }
      
    } catch (err) {
      console.error('Bulk certificate issuance error:', err);
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
                    <li>Required columns: student_name, course_name, institution</li>
                    <li>Optional columns: roll_no, year_of_passing, department, grade</li>
                    <li>First row should contain column headers</li>
                    <li>Maximum 1000 certificates per upload</li>
                  </ul>
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
                    {error}
                  </div>
                )}

                {bulkResults && (
                  <div className={`border rounded-md p-4 ${
                    (bulkResults.successful?.length || 0) > 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                  }`}>
                    <h4 className={`text-sm font-medium mb-2 ${
                      (bulkResults.successful?.length || 0) > 0 ? 'text-green-800' : 'text-red-800'
                    }`}>
                      Processing Results:
                    </h4>
                    <div className={`text-sm space-y-2 ${
                      (bulkResults.successful?.length || 0) > 0 ? 'text-green-700' : 'text-red-700'
                    }`}>
                      <div>Total processed: {bulkResults.total}</div>
                      <div>✅ Successful: {bulkResults.successful?.length || 0}</div>
                      <div>❌ Failed: {bulkResults.failed?.length || 0}</div>
                      
                      {/* Show development mode notice for mock certificates */}
                      {(bulkResults.successful?.length || 0) > 0 && (
                        <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-blue-700 text-xs">
                          📝 <strong>Development Mode:</strong> These are mock certificates for testing. 
                          In production, they would be stored in the database with real QR codes.
                        </div>
                      )}
                      
                      {bulkResults.successful?.length > 0 && (
                        <div className="mt-4">
                          <h5 className="font-medium">Successfully processed certificates:</h5>
                          <ul className="mt-2 space-y-1 max-h-32 overflow-y-auto">
                            {bulkResults.successful.slice(0, 5).map((cert, index) => (
                              <li key={index} className="text-xs flex justify-between">
                                <span>Row {cert.row}: {cert.certificate_id}</span>
                                <span className="text-blue-600 hover:underline cursor-pointer">
                                  View
                                </span>
                              </li>
                            ))}
                            {bulkResults.successful.length > 5 && (
                              <li className="text-xs font-medium">
                                ... and {bulkResults.successful.length - 5} more
                              </li>
                            )}
                          </ul>
                        </div>
                      )}
                      
                      {bulkResults.failed?.length > 0 && (
                        <div className="mt-4">
                          <h5 className="font-medium text-red-800">Failed certificates:</h5>
                          <ul className="mt-2 space-y-1 max-h-32 overflow-y-auto">
                            {bulkResults.failed.slice(0, 3).map((cert, index) => (
                              <li key={index} className="text-xs">
                                <div>Row {cert.row}: {cert.certificate_id}</div>
                                <div className="text-red-600 pl-2">Error: {cert.error}</div>
                              </li>
                            ))}
                            {bulkResults.failed.length > 3 && (
                              <li className="text-xs font-medium">
                                ... and {bulkResults.failed.length - 3} more errors
                              </li>
                            )}
                          </ul>
                        </div>
                      )}
                    </div>
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
              </p>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* QR Code Certificate */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-4">QR Certificate</h4>
                  <div className="border border-gray-200 rounded-lg p-4 text-center">
                    <img
                      src={issuanceResult.certificate_image_url}
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
                      <span className="text-sm font-medium">{singleCertData.student_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Roll No:</span>
                      <span className="text-sm font-medium">{singleCertData.roll_no}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Course:</span>
                      <span className="text-sm font-medium">{singleCertData.course_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Year:</span>
                      <span className="text-sm font-medium">{singleCertData.year_of_passing}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Certificate ID:</span>
                      <span className="text-sm font-medium font-mono">{issuanceResult.id}</span>
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
                        {issuanceResult.verification_url || 'Not available'}
                      </p>
                      <p className="text-xs text-gray-500 mt-2">
                        Scan QR code above or visit URL to verify
                      </p>
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
                    onClick={handleSendToStudent}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Send to Student
                    <Send className="h-4 w-4 ml-2" />
                  </button>
                  <button
                    onClick={handleDownloadCertificate}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    Download PDF
                    <Download className="h-4 w-4 ml-2" />
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