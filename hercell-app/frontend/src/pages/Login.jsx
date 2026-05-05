import Button from '../components/Button';
import Input from '../components/Input';
import { Link, useNavigate } from 'react-router-dom';
import { showErrorMessage } from '../utils/miscUtils';
import toast from 'react-hot-toast';
import { useAuth } from '../AuthContext';
import { useEffect, useState } from 'react';

const ForgotPasswordModal = ({ isOpen, onClose, initialEmail = '' }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const { sendResetPasswordEmail } = useAuth();

  useEffect(() => {
    if (isOpen) setEmail(initialEmail);
  }, [isOpen, initialEmail]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await sendResetPasswordEmail(email);
      toast.success('Please check your email for a link to reset your password.');
      onClose();
    } catch (error) {
      showErrorMessage(error, 'Failed to reset password, please double check the email you entered.');
    }
    setLoading(false);
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Reset password</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>
        <p className="text-sm text-gray-600 mb-6">
          We'll send you a link to reset your password
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            id="modal-email"
            label="Email"
            name="email"
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            required
            type="email"
            value={email}
          />
          <div className="flex space-x-3">
            <Button
              className="flex-1"
              disabled={loading}
              type="submit"
            >
              Send link
            </Button>
            <Button
              className="flex-1"
              onClick={onClose}
              type="button"
              variant="secondary"
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(formData);
      navigate('/');
    } catch(error) {
      showErrorMessage(error, 'Log in failed, please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
            Log in
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <Link
              className="font-medium text-blue-600 hover:text-blue-500"
              to="/signup"
            >
              Sign up
            </Link>
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div className="space-y-4">
            <Input
              id="email"
              label="Email"
              name="email"
              onChange={handleChange}
              placeholder="Email"
              required
              type="email"
              value={formData.email}
            />
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
          </div>
          <Button
            className="w-full"
            disabled={loading}
            type="submit"
          >
            Log in
          </Button>
        </form>
        <p className="mt-2 text-center text-sm text-gray-600">
          Forgot your password?{' '}
          <button
            className="font-medium text-blue-600 hover:text-blue-500"
            onClick={() => setShowForgotPasswordModal(true)}
          >
            Reset it
          </button>
        </p>
      </div>
      <ForgotPasswordModal
        initialEmail={formData.email}
        isOpen={showForgotPasswordModal}
        onClose={() => setShowForgotPasswordModal(false)}
      />
    </div>
  );
};

export default Login;
