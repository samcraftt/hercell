import Button from '../components/Button';
import Input from '../components/Input';
import passwordHelper from '../utils/passwordHelper';
import { showErrorMessage } from '../utils/miscUtils';
import toast from 'react-hot-toast';
import { useAuth } from '../AuthContext';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useState } from 'react';

const ResetPassword = () => {
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [passwordSecurity, setPasswordSecurity] = useState(passwordHelper.defaultSecurity);
  const [searchParams] = useSearchParams();
  const { resetPassword, verifyEmail } = useAuth();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));
    if (name === 'password' || name === 'confirmPassword') {
      const password = name === 'password' ? value : formData.password;
      const confirmPassword = name === 'confirmPassword' ? value : formData.confirmPassword;
      setPasswordSecurity(passwordHelper.getSecurity(password, confirmPassword));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
        const token = searchParams.get('token');
        const userId = searchParams.get('userId');
        if (!token || !userId) {
          toast.error('Invalid link, please request a new one.');
          navigate('/login');
          return;
        }
        await verifyEmail({ token, userId });
        await resetPassword(formData.password);
        toast.success('Password updated');
        navigate('/');
    } catch(error) {
        showErrorMessage(error, 'Failed to reset password, please try again.');
    }
    setLoading(false);
  };

  const isPasswordSecure = () => {
    return Object.values(passwordSecurity).every(Boolean);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
        Reset password
        </h2>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              id="password"
              label="Password"
              name="password"
              onChange={handleChange}
              placeholder="Password"
              required
              type="password"
              value={formData.password}
            />
            <Input
              id="confirmPassword"
              label="Confirm password"
              name="confirmPassword"
              onChange={handleChange}
              placeholder="Confirm password"
              required
              type="password"
              value={formData.confirmPassword}
            />
          </div>
          {passwordHelper.requirementsDisplay(passwordSecurity)}
          <Button
            className="w-full"
            disabled={loading || !isPasswordSecure()}
            type="submit"
          >
            Reset password
          </Button>
        </form>
      </div>
    </div>
  );
};

export default ResetPassword;
