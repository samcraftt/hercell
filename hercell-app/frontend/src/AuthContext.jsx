import { auth } from './api';
import { createContext, useContext, useEffect, useState } from 'react';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    const user = await auth.checkAuth();
    setUser(user || null);
    setLoading(false);
  };

  // Affects user object, so checkAuth
  const login = async (data) => {
    await auth.login(data);
    await checkAuth();
  };

  // Affects user object, so checkAuth
  const logout = async () => {
    await auth.logout();
    await checkAuth();
  };

  // Affects user object, so checkAuth
  const resetPassword = async (password) => {
    await auth.resetPassword(password);
    await checkAuth();
  }

  const sendResetPasswordEmail = async (email) => await auth.sendResetPasswordEmail(email);

  const signup = async (data) => await auth.signup(data);

  // Affects user object, so checkAuth
  const verifyEmail = async (data) => {
    await auth.verifyEmail(data);
    await checkAuth();
  }

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        checkAuth,
        login,
        logout,
        resetPassword,
        sendResetPasswordEmail,
        signup,
        verifyEmail
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
