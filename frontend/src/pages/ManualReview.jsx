import React, { useState, useEffect } from 'react';
import { Search, Filter, Eye, CheckCircle, XCircle, Clock, Building, GraduationCap, ArrowLeft, User, Award, Calendar, Hash, AlertTriangle, FileText } from 'lucide-react';

const ManualReview = () => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending'); // pending, all, approved, rejected
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedReview, setSelectedReview] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/admin/legacy-queue`);
        const data = await response.json();
        setReviews(data.requests || []);
      } catch (error) {
        console.error('Failed to fetch legacy verification requests:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [filter, searchTerm]);


  const handleReviewDecision = async (requestId, approved, notes, correctedFields = null) => {
    try {
      const endpoint = approved ? '/admin/legacy/approve' : '/admin/legacy/reject';
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request_id: requestId,
          admin_notes: notes,
          rejection_reason: approved ? null : notes
        }),
      });

      if (response.ok) {
        // Refresh the list
        const refreshResponse = await fetch('/admin/legacy-queue');
        const refreshData = await refreshResponse.json();
        setReviews(refreshData.requests || []);
        setSelectedReview(null);
      } else {
        throw new Error('Failed to submit review decision');
      }
    } catch (error) {
      console.error('Error submitting review:', error);
      alert('Failed to submit review decision');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'approved':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'rejected':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredReviews = reviews.filter(review =>
    (review.id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (review.student_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (review.course_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (review.roll_no || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

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
                Legacy Verification Queue
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">University Admin</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Legacy Certificate Verification</h1>
          <p className="text-gray-600">Review and verify legacy certificate requests from students</p>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex space-x-4">
              <div className="flex items-center space-x-2">
                <Filter className="h-5 w-5 text-gray-400" />
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="pending">Pending Verification</option>
                  <option value="all">All Requests</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Search className="h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by ID, name, or institution..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 w-64 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading reviews...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Reviews List */}
            <div className="space-y-4">
              {filteredReviews.length === 0 ? (
                <div className="bg-white rounded-lg shadow-md p-8 text-center">
                  <p className="text-gray-500">No reviews found</p>
                </div>
              ) : (
                filteredReviews.map((review) => (
                  <div
                    key={review.id}
                    className={`bg-white rounded-lg shadow-md p-6 cursor-pointer transition-all ${
                      selectedReview?.id === review.id
                        ? 'ring-2 ring-blue-500'
                        : 'hover:shadow-lg'
                    }`}
                    onClick={() => setSelectedReview(review)}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(review.status)}
                        <span className="font-medium text-gray-900">
                          {review.id}
                        </span>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        review.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        review.status === 'approved' ? 'bg-green-100 text-green-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {review.status.toUpperCase()}
                      </span>
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex items-center">
                        <User className="h-4 w-4 mr-2 text-gray-400" />
                        <span className="text-gray-500">Name: </span>
                        <span className="font-medium ml-1">{review.student_name || 'N/A'}</span>
                      </div>
                      <div className="flex items-center">
                        <Hash className="h-4 w-4 mr-2 text-gray-400" />
                        <span className="text-gray-500">Roll No: </span>
                        <span className="font-medium ml-1">{review.roll_no || 'N/A'}</span>
                      </div>
                      <div className="flex items-center">
                        <GraduationCap className="h-4 w-4 mr-2 text-gray-400" />
                        <span className="text-gray-500">Course: </span>
                        <span className="font-medium ml-1">{review.course_name || 'N/A'}</span>
                      </div>
                      <div className="flex items-center">
                        <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                        <span className="text-gray-500">Year: </span>
                        <span className="font-medium ml-1">{review.year_of_passing || 'N/A'}</span>
                      </div>
                    </div>

                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs text-gray-500 mb-1">Submitted:</p>
                      <p className="text-xs text-gray-700">
                        {new Date(review.submitted_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Review Details Panel */}
            <div className="lg:sticky lg:top-8">
              {selectedReview ? (
                <ReviewDetailPanel
                  review={selectedReview}
                  onDecision={handleReviewDecision}
                />
              ) : (
                <div className="bg-white rounded-lg shadow-md p-8 text-center">
                  <Eye className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-500">Select a review to view details</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const ReviewDetailPanel = ({ review, onDecision }) => {
  const [notes, setNotes] = useState('');
  const [editedFields, setEditedFields] = useState({
    student_name: review.student_name,
    roll_no: review.roll_no,
    course_name: review.course_name,
    year_of_passing: review.year_of_passing
  });
  const [isEditing, setIsEditing] = useState(false);

  const handleApprove = () => {
    if (!notes.trim()) {
      alert('Please add review notes');
      return;
    }
    onDecision(review.id, true, notes, isEditing ? editedFields : null);
  };

  const handleReject = () => {
    if (!notes.trim()) {
      alert('Please add rejection reason');
      return;
    }
    onDecision(review.id, false, notes);
  };

  const handleFieldChange = (field, value) => {
    setEditedFields(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Legacy Verification Details</h3>

      {/* Certificate Image */}
      {review.image_url && (
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-900 mb-2">Uploaded Certificate</h4>
          <img
            src={review.image_url}
            alt="Legacy Certificate"
            className="w-full rounded-lg border border-gray-200"
          />
        </div>
      )}

      {/* Student Information */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">Student Information</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Name:</span>
            <span className="font-medium">{review.student_name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Roll No:</span>
            <span className="font-medium">{review.roll_no}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Course:</span>
            <span className="font-medium">{review.course_name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Year:</span>
            <span className="font-medium">{review.year_of_passing}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Email:</span>
            <span className="font-medium">{review.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Phone:</span>
            <span className="font-medium">{review.phone || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Verification Instructions */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-2">Verification Instructions</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Cross-check student details with university archives</li>
          <li>• Verify certificate authenticity and format</li>
          <li>• Check for any discrepancies in information</li>
          <li>• If valid: Approve and generate QR code</li>
          <li>• If invalid: Reject with clear reason</li>
        </ul>
      </div>

      {/* Admin Notes */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Admin Notes *
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={4}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Add your verification notes..."
        />
      </div>


      {/* Action Buttons */}
      <div className="flex space-x-3">
        <button
          onClick={handleApprove}
          className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors flex items-center justify-center space-x-2"
        >
          <CheckCircle className="h-4 w-4" />
          <span>Approve & Generate QR</span>
        </button>
        <button
          onClick={handleReject}
          className="flex-1 bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 transition-colors flex items-center justify-center space-x-2"
        >
          <XCircle className="h-4 w-4" />
          <span>Reject</span>
        </button>
      </div>
    </div>
  );
};

export default ManualReview;
