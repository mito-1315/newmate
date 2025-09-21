import React, { useState } from 'react';
import { FileText, Upload, Download, Send, Plus, Eye, CheckCircle } from 'lucide-react';

const UniversityAdmin = () => {
  const [activeTab, setActiveTab] = useState('issue');
  const [formData, setFormData] = useState({
    student_name: '',
    roll_no: '',
    course_name: '',
    institution_name: '',
    year_of_passing: '',
    department: '',
    grade: '',
    additional_fields: {}
  });
  const [certificateImage, setCertificateImage] = useState(null);
  const [generatedCertificate, setGeneratedCertificate] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    console.log(`Form field changed: ${name} = ${value}`);
    setFormData(prev => {
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

  const handleIssueCertificate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('Starting certificate issuance...');
      console.log('Form data:', formData);
      console.log('Certificate image:', certificateImage);
      
      // Validate required fields before sending
      const requiredFields = ['student_name', 'course_name', 'institution_name'];
      const missingFields = requiredFields.filter(field => !formData[field]);
      
      if (missingFields.length > 0) {
        throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
      }
      
      const formDataToSend = new FormData();
      formDataToSend.append('file', certificateImage);
      formDataToSend.append('certificate_data', JSON.stringify(formData));
      
      console.log('Making request to /issue/certificate...');
      const response = await fetch('/issue/certificate', {
        method: 'POST',
        body: formDataToSend,
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (response.ok) {
        const result = await response.json();
        console.log('Success result:', result);
        setGeneratedCertificate(result);
        setActiveTab('preview');
      } else {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`Failed to issue certificate: ${response.statusText} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error issuing certificate:', error);
      alert(`Failed to issue certificate: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadCertificate = () => {
    if (generatedCertificate) {
      // Create download link for PDF
      const link = document.createElement('a');
      link.href = generatedCertificate.pdf_url;
      link.download = `certificate_${formData.rollNo}.pdf`;
      link.click();
    }
  };

  const handleSendToStudent = async () => {
    if (generatedCertificate) {
      try {
        const response = await fetch('/issue/send-email', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            certificate_id: generatedCertificate.id,
            student_email: formData.studentEmail,
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
    { id: 'issue', name: 'Issue New Certificate', icon: Plus },
    { id: 'preview', name: 'Certificate Preview', icon: Eye },
    { id: 'queue', name: 'Legacy Verification Queue', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <FileText className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">
                University Admin Dashboard
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Welcome, Admin</span>
              <button className="text-sm text-blue-600 hover:text-blue-500">
                Sign Out
              </button>
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
        {activeTab === 'issue' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Issue New Certificate</h3>
              <p className="mt-1 text-sm text-gray-500">
                Fill in the student details and upload the certificate image
              </p>
            </div>
            <form onSubmit={handleIssueCertificate} className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Student Name *
                  </label>
                  <input
                    type="text"
                    name="student_name"
                    value={formData.student_name}
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
                    value={formData.roll_no}
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
                    value={formData.course_name}
                    onChange={handleInputChange}
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter course name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Institution Name *
                  </label>
                  <input
                    type="text"
                    name="institution_name"
                    value={formData.institution_name}
                    onChange={handleInputChange}
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter institution name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Year of Passing *
                  </label>
                  <input
                    type="number"
                    name="year_of_passing"
                    value={formData.year_of_passing}
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
                    Department
                  </label>
                  <input
                    type="text"
                    name="department"
                    value={formData.department}
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
                    value={formData.grade}
                    onChange={handleInputChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter grade or CGPA"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Certificate Image *
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600">
                      <label className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                        <span>Upload a file</span>
                        <input
                          type="file"
                          accept="image/*,.pdf"
                          onChange={handleImageUpload}
                          className="sr-only"
                          required
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

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !certificateImage}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {loading ? 'Generating...' : 'Generate Certificate'}
                </button>
              </div>
            </form>
          </div>
        )}

        {activeTab === 'preview' && generatedCertificate && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Certificate Preview</h3>
              <p className="mt-1 text-sm text-gray-500">
                Review the generated certificate before finalizing
              </p>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Certificate Image */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-4">Certificate Image</h4>
                  <div className="border border-gray-200 rounded-lg p-4">
                    <img
                      src={generatedCertificate.image_url}
                      alt="Generated Certificate"
                      className="w-full h-auto rounded"
                    />
                  </div>
                </div>

                {/* Certificate Details */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-4">Certificate Details</h4>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Student Name:</span>
                      <span className="text-sm font-medium">{formData.studentName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Roll No:</span>
                      <span className="text-sm font-medium">{formData.rollNo}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Course:</span>
                      <span className="text-sm font-medium">{formData.courseName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Year:</span>
                      <span className="text-sm font-medium">{formData.yearOfPassing}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Certificate ID:</span>
                      <span className="text-sm font-medium font-mono">{generatedCertificate.id}</span>
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
                    <h5 className="text-sm font-medium text-gray-900 mb-2">QR Code</h5>
                    <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
                      <img
                        src={generatedCertificate.qr_code_url}
                        alt="QR Code"
                        className="w-32 h-32 mx-auto"
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        Scan to verify certificate
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-6 flex justify-between">
                <button
                  onClick={() => setActiveTab('issue')}
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

        {activeTab === 'queue' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Legacy Verification Queue</h3>
              <p className="mt-1 text-sm text-gray-500">
                Review and verify legacy certificate requests
              </p>
            </div>
            <div className="p-6">
              <div className="text-center py-12">
                <FileText className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No pending requests</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Legacy verification requests will appear here
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UniversityAdmin;
