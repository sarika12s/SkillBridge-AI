import React, { useState, useEffect } from 'react';
import { LogIn, LogOut, ShieldAlert } from 'lucide-react';
import { getCurrentUser, loginUser, registerUser, clearToken, getStoredToken, type UserProfile } from '../../services/authService';

export const AuthBanner: React.FC<{ onAuthChange?: () => void }> = ({ onAuthChange }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [, setLoading] = useState<boolean>(true);
  const [showModal, setShowModal] = useState<boolean>(false);
  const [isRegister, setIsRegister] = useState<boolean>(false);
  const [email, setEmail] = useState<string>('student@college.edu');
  const [password, setPassword] = useState<string>('StudentPass123!');
  const [fullName, setFullName] = useState<string>('Alex Carter');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const checkAuth = async () => {
    setLoading(true);
    const token = getStoredToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const profile = await getCurrentUser();
      setUser(profile);
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      if (isRegister) {
        await registerUser(email, password, fullName);
      } else {
        await loginUser(email, password);
      }
      setShowModal(false);
      await checkAuth();
      if (onAuthChange) onAuthChange();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Authentication failed.');
    }
  };

  const handleLogout = () => {
    clearToken();
    setUser(null);
    if (onAuthChange) onAuthChange();
  };

  const handleQuickDemoLogin = async () => {
    setErrorMsg(null);
    try {
      // Attempt login first
      await loginUser('student@college.edu', 'StudentPass123!');
      await checkAuth();
      if (onAuthChange) onAuthChange();
    } catch {
      // If demo user does not exist, auto-register
      try {
        await registerUser('student@college.edu', 'StudentPass123!', 'Alex Carter (Demo Student)');
        await checkAuth();
        if (onAuthChange) onAuthChange();
      } catch (err: any) {
        setErrorMsg(err?.response?.data?.detail || 'Demo login failed.');
      }
    }
  };

  return (
    <>
      <div className="bg-white border border-slate-200 rounded-xl p-3.5 px-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-sm">
        <div className="flex items-center space-x-2">
          {user ? (
            <>
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-slate-600">Authenticated Session:</span>
              <span className="font-bold text-slate-800">{user.full_name}</span>
              <span className="text-slate-400 font-mono">({user.email})</span>
            </>
          ) : (
            <>
              <ShieldAlert className="w-4 h-4 text-amber-500" />
              <span className="text-slate-600 font-medium">
                Not logged in. An authenticated session is required to upload and parse resumes.
              </span>
            </>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {user ? (
            <button
              onClick={handleLogout}
              className="text-xs text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          ) : (
            <>
              <button
                onClick={handleQuickDemoLogin}
                className="text-xs text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 font-medium px-3 py-1.5 rounded-lg transition"
              >
                1-Click Demo Login
              </button>
              <button
                onClick={() => setShowModal(true)}
                className="text-xs text-white bg-blue-600 hover:bg-blue-700 font-medium px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In / Register</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Auth Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 sm:p-8 shadow-xl space-y-5 border border-slate-200">
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-slate-900">
                {isRegister ? 'Create Student Account' : 'Sign in to SkillBridge AI'}
              </h3>
              <p className="text-xs text-slate-500">
                {isRegister
                  ? 'Register to upload resumes and perform semantic matching.'
                  : 'Enter your credentials to continue.'}
              </p>
            </div>

            <form onSubmit={handleAuthSubmit} className="space-y-4 text-xs">
              {isRegister && (
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Full Name</label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              )}

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Email Address</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full text-sm p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              {errorMsg && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs">
                  {errorMsg}
                </div>
              )}

              <div className="flex items-center justify-between pt-2">
                <button
                  type="button"
                  onClick={() => setIsRegister(!isRegister)}
                  className="text-blue-600 hover:underline"
                >
                  {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Register"}
                </button>
                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold shadow-sm"
                  >
                    {isRegister ? 'Register' : 'Sign In'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
