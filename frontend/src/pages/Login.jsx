import React, { useState } from 'react';
import { User, Lock, Mail, Eye, EyeOff, Shield, GraduationCap, Building, Briefcase } from 'lucide-react';

const Login = ({ onAuthSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'student',
    institution: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    console.log('Input change:', name, value);
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Predefined users for testing
  const predefinedUsers = {
    'admin@test.com': {
      password: 'admin123',
      role: 'university_admin',
      full_name: 'University Admin',
      institution: 'Test University'
    },
    'student@test.com': {
      password: 'student123',
      role: 'student',
      full_name: 'Test Student',
      institution: 'Test University'
    },
    'employer@test.com': {
      password: 'employer123',
      role: 'employer',
      full_name: 'Test Employer',
      institution: 'Test Company'
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    console.log('Form data on submit:', formData);
    console.log('Is login:', isLogin);

    try {
      if (isLogin) {
        // Validate required fields
        if (!formData.email || !formData.password) {
          throw new Error('Email and password are required');
        }
        
        if (!formData.role) {
          throw new Error('Please select a role');
        }
        
        // Check if user exists in predefined users
        const user = predefinedUsers[formData.email];
        if (!user) {
          throw new Error('Invalid email address');
        }
        
        // Check password
        if (user.password !== formData.password) {
          throw new Error('Invalid password');
        }
        
        // Check if selected role matches user's role
        if (user.role !== formData.role) {
          throw new Error(`This email is registered as ${user.role.replace('_', ' ')}. Please select the correct role.`);
        }
        
        // Create user data
        const userData = {
          id: user.role === 'university_admin' ? '1' : user.role === 'student' ? '2' : '3',
          full_name: user.full_name,
          email: formData.email,
          role: user.role,
          institution: user.institution
        };
        
        console.log('Creating user data:', userData);
        onAuthSuccess(userData);
      } else {
        // Registration
        if (!formData.full_name || !formData.email || !formData.password) {
          throw new Error('All fields are required');
        }
        
        const userData = {
          id: Date.now().toString(),
          full_name: formData.full_name,
          email: formData.email,
          role: formData.role,
          institution: formData.institution || 'Default Institution'
        };
        
        onAuthSuccess(userData);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'university_admin':
        return <Building className="h-5 w-5" />;
      case 'student':
        return <GraduationCap className="h-5 w-5" />;
      case 'employer':
        return <Briefcase className="h-5 w-5" />;
      default:
        return <User className="h-5 w-5" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <Shield className="h-12 w-12 text-blue-600" />
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          {isLogin ? 'Sign in to your account' : 'Create your account'}
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Certificate Verification System
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {!isLogin && (
              <div>
                <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                  Full Name
                </label>
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  required={!isLogin}
                  value={formData.full_name}
                  onChange={handleInputChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Enter your full name"
                />
              </div>
            )}

            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700">
                Role
              </label>
              <div className="text-xs text-gray-500 mb-2">
                Selected: {formData.role || 'None'}
              </div>
              <div className="mt-1 grid grid-cols-3 gap-3">
                {[
                  { value: 'student', label: 'Student', icon: GraduationCap },
                  { value: 'university_admin', label: 'University Admin', icon: Building },
                  { value: 'employer', label: 'Employer/Verifier', icon: Briefcase }
                ].map((role) => {
                  const Icon = role.icon;
                  return (
                    <label key={role.value} className="relative">
                      <input
                        type="radio"
                        name="role"
                        value={role.value}
                        checked={formData.role === role.value}
                        onChange={(e) => {
                          console.log('Role selected:', e.target.value);
                          handleInputChange(e);
                        }}
                        className="sr-only"
                      />
                      <div className={`cursor-pointer rounded-lg p-3 text-center border-2 transition-colors ${
                        formData.role === role.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}>
                        <Icon className="h-6 w-6 mx-auto mb-1" />
                        <div className="text-xs font-medium">{role.label}</div>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            {formData.role === 'university_admin' && (
              <div>
                <label htmlFor="institution" className="block text-sm font-medium text-gray-700">
                  Institution Name
                </label>
                <input
                  id="institution"
                  name="institution"
                  type="text"
                  required={formData.role === 'university_admin'}
                  value={formData.institution}
                  onChange={handleInputChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Enter institution name"
                />
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleInputChange}
                  className="appearance-none block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Enter your email"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="appearance-none block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Enter your password"
                />
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-gray-400 hover:text-gray-500"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}

            {/* Test Credentials */}
            <div className="bg-blue-50 border border-blue-200 p-3 rounded text-xs">
              <strong>Test Credentials:</strong><br/>
              <div className="mt-1 space-y-1">
                <div><strong>University Admin:</strong> admin@test.com / admin123</div>
                <div><strong>Student:</strong> student@test.com / student123</div>
                <div><strong>Employer:</strong> employer@test.com / employer123</div>
              </div>
            </div>

            {/* Debug section */}
            <div className="bg-gray-100 p-3 rounded text-xs">
              <strong>Debug Info:</strong><br/>
              Email: {formData.email}<br/>
              Role: {formData.role}<br/>
              Is Login: {isLogin.toString()}
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? 'Processing...' : (isLogin ? 'Sign in' : 'Sign up')}
              </button>
            </div>

            <div className="text-center">
              <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                className="text-blue-600 hover:text-blue-500 text-sm"
              >
                {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;