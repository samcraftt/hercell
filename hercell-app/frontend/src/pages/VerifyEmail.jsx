import { showErrorMessage } from '../utils/miscUtils';
import { toast } from 'react-hot-toast';
import { useAuth } from '../AuthContext';
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const VerifyEmail = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { verifyEmail } = useAuth();

  useEffect(() => {
    const verify = async () => {
      try {
        const token = searchParams.get('token');
        const userId = Number(searchParams.get('userId'));
        if (!token || !userId) {
          toast.error('Invalid verification link. Please try logging in again.');
          navigate('/login');
          return;
        }
        await verifyEmail({ token, userId });
        toast.success('Email verified successfully! Redirecting to home...');
        setTimeout(() => navigate('/'), 2000);
      } catch (error) {
        showErrorMessage(error, 'Failed to verify email. Please try logging in again.');
        navigate('/login');
      }
    };
    verify();
  }, [navigate, searchParams, verifyEmail]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <h2 className="text-2xl font-bold tracking-tight text-gray-900">
        Verifying your email...
      </h2>
    </div>
  );
};

export default VerifyEmail;
