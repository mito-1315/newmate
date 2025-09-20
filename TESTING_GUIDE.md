# Certificate Verification System - Complete Testing Guide

## 🎯 System Overview

This comprehensive certificate verification system supports both **new digital certificates** and **legacy certificate verification** with role-based access for different user types.

### User Roles & Access
- **University Admin**: Issue new certificates, review legacy verification requests
- **Student**: View issued certificates, request legacy verification
- **Employer/Verifier**: Scan QR codes for public verification

---

## 🚀 Quick Start Testing

### 1. Start Backend Server
```bash
cd backend
python -m app.main
```
**Expected**: Server running on `http://localhost:8000`

### 2. Start Frontend Development Server
```bash
cd frontend
npm start
```
**Expected**: Frontend running on `http://localhost:3000`

---

## 🔐 Authentication Testing

### Test User Registration & Login

1. **Open** `http://localhost:3000`
2. **You should see** the authentication page
3. **Test Registration**:
   - Click "Don't have an account? Sign up"
   - Fill in details:
     - Name: `Test Admin`
     - Role: `University Admin`
     - Institution: `Test University`
     - Email: `admin@test.com`
     - Password: `password123`
   - Click "Sign up"
   - **Expected**: Success message or email verification prompt

4. **Test Login**:
   - Use the same credentials
   - Click "Sign in"
   - **Expected**: Redirected to University Admin Dashboard

---

## 🏛️ University Admin Workflow Testing

### A. Issue New Certificate

1. **Login as University Admin**
2. **Navigate to "Issue New Certificate" tab**
3. **Fill Certificate Form**:
   - Student Name: `John Doe`
   - Roll No: `CS2023001`
   - Course Name: `Computer Science`
   - Year of Passing: `2023`
   - Department: `Computer Science`
   - Grade: `A+`
4. **Upload Certificate Image**:
   - Click "Upload a file"
   - Select a certificate image (JPG/PNG/PDF)
5. **Click "Generate Certificate"**
6. **Expected Results**:
   - Loading state during processing
   - Redirect to "Certificate Preview" tab
   - Display certificate image with QR code
   - Show certificate details
   - "Download PDF" and "Send to Student" buttons

### B. Legacy Verification Queue

1. **Navigate to "Legacy Verification Queue" tab**
2. **Expected**: Table showing pending legacy verification requests
3. **Test Actions**:
   - View uploaded certificate image
   - Approve/Reject requests
   - Add admin notes

---

## 🎓 Student Portal Testing

### A. View Certificates

1. **Login as Student** (create student account first)
2. **Expected**: "My Certificates" page with card view
3. **Test Certificate Cards**:
   - Each card shows: Course name, Institution, Year, Grade
   - QR code preview
   - "View" and "Download" buttons

### B. Request Legacy Verification

1. **Click "Request Legacy Verification"**
2. **Fill Legacy Form**:
   - Full Name: `Jane Smith`
   - Roll No: `CS2022001`
   - Course Name: `Computer Science`
   - Year of Passing: `2022`
   - Email: `jane@email.com`
   - Phone: `+1234567890`
3. **Upload Legacy Certificate Image**
4. **Click "Submit Verification Request"**
5. **Expected**: Success message with request ID

---

## 🔍 Public Verification Testing

### A. QR Code Verification

1. **Open** `http://localhost:3000/verify/{attestation_id}`
2. **Replace `{attestation_id}`** with a valid certificate ID
3. **Expected Results**:
   - Loading state during verification
   - ✅ "Certificate Verified" status
   - Detailed certificate information
   - Certificate image display
   - QR code for sharing

### B. Test Invalid Certificate

1. **Open** `http://localhost:3000/verify/invalid_id`
2. **Expected**: ❌ "Verification Failed" with error message

---

## 📊 Dashboard & Analytics Testing

### A. Admin Dashboard

1. **Login as University Admin**
2. **Navigate to Dashboard** (if available)
3. **Expected**: Statistics cards showing:
   - Total certificates issued
   - Verification success rate
   - Recent activity

### B. Manual Review Queue

1. **Navigate to "Reviews" tab**
2. **Expected**: Table of certificates pending manual review
3. **Test Actions**:
   - Filter by status (pending, approved, rejected)
   - Search by student name
   - Click on certificate for detailed view
   - Approve/Reject with notes

---

## 🔧 API Endpoint Testing

### Test Backend Endpoints Directly

```bash
# Health check
curl http://localhost:8000/

# Upload certificate
curl -X POST -F "file=@certificate.jpg" http://localhost:8000/upload

# Get verification stats
curl http://localhost:8000/analytics/verification-stats

# Issue new certificate
curl -X POST -F "file=@certificate.jpg" -F "certificate_data={\"student_name\":\"Test Student\"}" http://localhost:8000/issue/certificate

# Get student certificates
curl http://localhost:8000/student/certificates

# Submit legacy verification
curl -X POST -F "file=@legacy_cert.jpg" -F "verification_data={\"student_name\":\"Legacy Student\"}" http://localhost:8000/legacy/verify
```

---

## 🐛 Common Issues & Troubleshooting

### Frontend Issues

1. **"Cannot read properties of undefined" errors**:
   - **Solution**: Check if API responses match expected data structure
   - **Fix**: Added null checks in components

2. **API calls failing with 404/500**:
   - **Solution**: Ensure backend is running on port 8000
   - **Check**: API endpoints match frontend calls

3. **Authentication not working**:
   - **Solution**: Check Supabase configuration
   - **Verify**: Environment variables are set correctly

### Backend Issues

1. **"Module not found" errors**:
   - **Solution**: Install missing dependencies
   - **Run**: `pip install -r requirements.txt`

2. **Database connection issues**:
   - **Solution**: Check Supabase credentials
   - **Verify**: `.env` file has correct values

3. **Image processing errors**:
   - **Solution**: Ensure uploaded files are valid images
   - **Check**: File size limits and formats

---

## 📱 Mobile Testing

### Test Responsive Design

1. **Open browser developer tools**
2. **Switch to mobile view** (iPhone/Android)
3. **Test all pages**:
   - Authentication forms
   - Certificate upload
   - Dashboard cards
   - QR code scanning

### Test QR Code Scanning

1. **Generate a certificate with QR code**
2. **Use mobile device camera** to scan QR
3. **Expected**: Redirects to verification page
4. **Test**: Verification works on mobile

---

## 🎨 UI/UX Testing

### Visual Design Testing

1. **Check all pages load correctly**
2. **Verify consistent styling** across components
3. **Test hover states** and button interactions
4. **Check loading states** during API calls
5. **Verify error messages** are user-friendly

### Accessibility Testing

1. **Test keyboard navigation**
2. **Check color contrast** for readability
3. **Verify screen reader compatibility**
4. **Test form validation** messages

---

## 📈 Performance Testing

### Load Testing

1. **Upload multiple certificates** simultaneously
2. **Test with large image files** (10MB+)
3. **Monitor response times** for API calls
4. **Check memory usage** during processing

### Database Performance

1. **Test with large datasets** (1000+ certificates)
2. **Monitor query performance**
3. **Check pagination** for large lists

---

## 🔒 Security Testing

### Authentication Security

1. **Test password requirements**
2. **Verify session management**
3. **Check role-based access control**
4. **Test logout functionality**

### Data Security

1. **Verify file upload security**
2. **Check data validation**
3. **Test SQL injection prevention**
4. **Verify CORS configuration**

---

## ✅ Complete Test Checklist

### Frontend Testing
- [ ] Authentication (login/signup/logout)
- [ ] University Admin Dashboard
- [ ] Student Portal
- [ ] Legacy Verification Request
- [ ] Public Verification Page
- [ ] Responsive Design
- [ ] Error Handling
- [ ] Loading States

### Backend Testing
- [ ] API Endpoints (all routes)
- [ ] File Upload Processing
- [ ] Database Operations
- [ ] Error Handling
- [ ] Authentication Middleware
- [ ] CORS Configuration

### Integration Testing
- [ ] Frontend-Backend Communication
- [ ] Database Integration
- [ ] File Storage
- [ ] QR Code Generation
- [ ] Email Notifications (mock)

### User Workflow Testing
- [ ] Complete University Admin Flow
- [ ] Complete Student Flow
- [ ] Complete Employer Verification Flow
- [ ] Legacy Certificate Workflow
- [ ] Error Recovery Scenarios

---

## 🚀 Production Deployment Checklist

### Environment Setup
- [ ] Configure production Supabase instance
- [ ] Set up proper environment variables
- [ ] Configure CORS for production domain
- [ ] Set up file storage (Supabase Storage)
- [ ] Configure email service

### Security
- [ ] Enable HTTPS
- [ ] Configure proper CORS origins
- [ ] Set up rate limiting
- [ ] Enable input validation
- [ ] Configure file upload limits

### Monitoring
- [ ] Set up error logging
- [ ] Configure performance monitoring
- [ ] Set up database monitoring
- [ ] Configure backup procedures

---

## 📞 Support & Troubleshooting

### Getting Help
1. **Check browser console** for JavaScript errors
2. **Check backend logs** for server errors
3. **Verify network requests** in browser dev tools
4. **Check database** for data consistency

### Common Commands
```bash
# Restart backend
cd backend && python -m app.main

# Restart frontend
cd frontend && npm start

# Check logs
tail -f backend/logs/app.log

# Test API
curl http://localhost:8000/
```

---

## 🎉 Success Criteria

The system is working correctly when:

1. **All user roles can authenticate** and access their respective dashboards
2. **University admins can issue certificates** with QR codes
3. **Students can view their certificates** and request legacy verification
4. **Employers can verify certificates** by scanning QR codes
5. **Legacy verification workflow** functions end-to-end
6. **All API endpoints** respond correctly
7. **UI is responsive** and user-friendly
8. **Error handling** works gracefully
9. **File uploads** process successfully
10. **Database operations** complete without errors

---

**Happy Testing! 🚀**

If you encounter any issues, check the troubleshooting section above or review the error logs for detailed information.
