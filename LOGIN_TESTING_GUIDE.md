# 🔐 Login Testing Guide

## Fixed Authentication Credentials

The application now has **fixed credentials** for testing. You can no longer login with any email/password combination.

### 📋 Test Credentials

| Role | Email | Password | Expected Redirect |
|------|-------|----------|-------------------|
| **University Admin** | `admin@test.com` | `admin123` | `/admin/dashboard` |
| **Student** | `student@test.com` | `student123` | `/student/dashboard` |
| **Employer/Verifier** | `employer@test.com` | `employer123` | `/verify` |

## 🧪 How to Test

### 1. **University Admin Login**
```
Email: admin@test.com
Password: admin123
Role: Select "University Admin"
```
**Expected Result:** Redirected to University Admin Dashboard

### 2. **Student Login**
```
Email: student@test.com
Password: student123
Role: Select "Student"
```
**Expected Result:** Redirected to Student Dashboard

### 3. **Employer/Verifier Login**
```
Email: employer@test.com
Password: employer123
Role: Select "Employer/Verifier"
```
**Expected Result:** Redirected to Verification Page

## ❌ Error Testing

### Invalid Email
```
Email: wrong@test.com
Password: admin123
Role: University Admin
```
**Expected Result:** "Invalid email address" error

### Wrong Password
```
Email: admin@test.com
Password: wrongpassword
Role: University Admin
```
**Expected Result:** "Invalid password" error

### Wrong Role Selection
```
Email: admin@test.com
Password: admin123
Role: Student
```
**Expected Result:** "This email is registered as university admin. Please select the correct role." error

### Missing Fields
```
Email: (empty)
Password: admin123
Role: University Admin
```
**Expected Result:** "Email and password are required" error

## 🔍 Debug Information

The login form now shows:
- **Test Credentials section** - Shows all available test accounts
- **Debug Info section** - Shows current form state
- **Console logs** - Detailed logging for troubleshooting

## 🚀 Quick Test Steps

1. **Open** `http://localhost:3000`
2. **See the test credentials** displayed on the login form
3. **Try each credential set** and verify correct redirection
4. **Test error cases** to ensure proper validation
5. **Check browser console** for detailed logs

## ✅ Success Indicators

- **Correct redirection** based on role
- **Navigation shows correct user info** (name and role)
- **No console errors**
- **Proper error messages** for invalid attempts

## 🐛 Troubleshooting

If login still doesn't work:
1. **Check browser console** for error messages
2. **Verify the debug info** shows correct values
3. **Clear browser cache** and try again
4. **Check that frontend is running** on port 3000
5. **Ensure backend is running** on port 8000

---

**Note:** These are test credentials only. In production, you would integrate with a proper authentication system like Supabase Auth, Auth0, or your own backend authentication.
