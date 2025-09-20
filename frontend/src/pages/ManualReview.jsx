import React, { useState, useEffect } from 'react';
import { Search, Filter, Eye, CheckCircle, XCircle, Clock } from 'lucide-react';

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
        const response = await fetch(`/api/reviews?status=${filter}&search=${searchTerm}`);
        const data = await response.json();
        setReviews(data.reviews || []);
      } catch (error) {
        console.error('Failed to fetch reviews:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [filter, searchTerm]);


  const handleReviewDecision = async (verificationId, approved, notes, correctedFields = null) => {
    try {
      const response = await fetch('/api/reviews/decision', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          verification_id: verificationId,
          approved,
          reviewer_notes: notes,
          corrected_fields: correctedFields,
        }),
      });

      if (response.ok) {
        // Refresh the list
        const refreshResponse = await fetch(`/api/reviews?status=${filter}&search=${searchTerm}`);
        const refreshData = await refreshResponse.json();
        setReviews(refreshData.reviews || []);
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
    review.verification_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    review.extracted_fields.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    review.extracted_fields.institution?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Manual Review Queue</h1>
          <p className="text-gray-600">Review certificates that require manual verification</p>
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
                  <option value="pending">Pending Reviews</option>
                  <option value="all">All Reviews</option>
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
                    key={review.verification_id}
                    className={`bg-white rounded-lg shadow-md p-6 cursor-pointer transition-all ${
                      selectedReview?.verification_id === review.verification_id
                        ? 'ring-2 ring-blue-500'
                        : 'hover:shadow-lg'
                    }`}
                    onClick={() => setSelectedReview(review)}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(review.status)}
                        <span className="font-medium text-gray-900">
                          {review.verification_id.substring(0, 12)}...
                        </span>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(review.risk_score.risk_level)}`}>
                        {review.risk_score.risk_level.toUpperCase()}
                      </span>
                    </div>

                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-gray-500">Name: </span>
                        <span className="font-medium">{review.extracted_fields.name || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Institution: </span>
                        <span className="font-medium">{review.extracted_fields.institution || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Course: </span>
                        <span className="font-medium">{review.extracted_fields.course_name || 'N/A'}</span>
                      </div>
                    </div>

                    {review.risk_score.factors.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs text-gray-500 mb-1">Risk Factors:</p>
                        <p className="text-xs text-red-600">
                          {review.risk_score.factors.slice(0, 2).join(', ')}
                          {review.risk_score.factors.length > 2 && '...'}
                        </p>
                      </div>
                    )}
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
  const [editedFields, setEditedFields] = useState(review.extracted_fields);
  const [isEditing, setIsEditing] = useState(false);

  const handleApprove = () => {
    if (!notes.trim()) {
      alert('Please add review notes');
      return;
    }
    onDecision(review.verification_id, true, notes, isEditing ? editedFields : null);
  };

  const handleReject = () => {
    if (!notes.trim()) {
      alert('Please add review notes');
      return;
    }
    onDecision(review.verification_id, false, notes);
  };

  const handleFieldChange = (field, value) => {
    setEditedFields(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Review Details</h3>

      {/* Certificate Image */}
      {review.image_url && (
        <div className="mb-6">
          <img
            src={review.image_url}
            alt="Certificate"
            className="w-full rounded-lg border border-gray-200"
          />
        </div>
      )}

      {/* Risk Assessment */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-2">Risk Assessment</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Overall Score: </span>
            <span className="font-medium">{Math.round(review.risk_score.overall_score * 100)}%</span>
          </div>
          <div>
            <span className="text-gray-500">Confidence: </span>
            <span className="font-medium">{Math.round(review.risk_score.confidence * 100)}%</span>
          </div>
        </div>
        {review.risk_score.factors.length > 0 && (
          <div className="mt-3">
            <p className="text-sm text-gray-500 mb-1">Risk Factors:</p>
            <ul className="text-sm text-gray-600 space-y-1">
              {review.risk_score.factors.map((factor, index) => (
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
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-gray-900">Extracted Fields</h4>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            {isEditing ? 'Cancel Edit' : 'Edit Fields'}
          </button>
        </div>

        <div className="space-y-3">
          {Object.entries(review.extracted_fields).map(([key, value]) => {
            if (key === 'additional_fields') return null;
            return (
              <div key={key}>
                <label className="block text-sm text-gray-500 mb-1 capitalize">
                  {key.replace('_', ' ')}
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editedFields[key] || ''}
                    onChange={(e) => handleFieldChange(key, e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                ) : (
                  <p className="font-medium text-sm">{value || 'N/A'}</p>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Review Notes */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Review Notes *
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={4}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Add your review comments..."
        />
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-3">
        <button
          onClick={handleApprove}
          className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors flex items-center justify-center space-x-2"
        >
          <CheckCircle className="h-4 w-4" />
          <span>Approve</span>
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
