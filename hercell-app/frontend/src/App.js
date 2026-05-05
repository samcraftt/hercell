import { AuthProvider, useAuth } from './AuthContext';
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom';
import Home from './pages/Home';
import Loading from './pages/Loading';
import Login from './pages/Login';
import NotFound from './pages/NotFound';
import ResetPassword from './pages/ResetPassword';
import Signup from './pages/Signup';
import toast from 'react-hot-toast';
import Toaster from './components/Toaster';
import VerifyEmail from './pages/VerifyEmail';

const PrivateRoutes = () => {
  const { loading, user } = useAuth();
  if (loading) return Loading;
  if (!user) {
    toast.error('Please log in');
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
};

const App = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/verify-email" element={<VerifyEmail />} />

          <Route element={<PrivateRoutes />}>
            <Route path="/private-route" element={<p>This is a private route</p>} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;