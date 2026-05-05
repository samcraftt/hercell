import Button from '../components/Button';
import Input from '../components/Input';
import passwordHelper from '../utils/passwordHelper';
import { showErrorMessage } from '../utils/miscUtils';
import { toast } from 'react-hot-toast';
import { useAuth } from '../AuthContext';
import { useState } from 'react';

const Signup = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [passwordSecurity, setPasswordSecurity] = useState(passwordHelper.defaultSecurity);
  const { signup } = useAuth();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (name === 'password' || name === 'confirmPassword') {
      const password = name === 'password' ? value : formData.password;
      const confirmPassword = name === 'confirmPassword' ? value : formData.confirmPassword;
      setPasswordSecurity(passwordHelper.getSecurity(password, confirmPassword));
    }
  };

  const isPasswordSecure = () => {
    return Object.values(passwordSecurity).every(Boolean);
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { confirmPassword, ...signupData } = formData;
      await signup(signupData);
      toast.success('Account created! Please check your email to verify your account.');
    } catch (error) {
      showErrorMessage(error, 'Sign up failed, please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
            Sign up
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Already have an account?{' '}
            <a
              className="font-medium text-blue-600 hover:text-blue-500"
              href="/login"
            >
              Log in
            </a>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSignup}>
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                id="firstName"
                label="First name"
                name="firstName"
                onChange={handleChange}
                placeholder="First name"
                required
                type="text"
                value={formData.firstName}
              />

              <Input
                id="lastName"
                label="Last name"
                name="lastName"
                onChange={handleChange}
                placeholder="Last name"
                required
                type="text"
                value={formData.lastName}
              />
            </div>

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

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
                type="password"
                value={formData.confirmPassword}
              />
            </div>

            {passwordHelper.requirementsDisplay(passwordSecurity)}
          </div>

          <Button
            className="w-full"
            disabled={loading || !isPasswordSecure()}
            type="submit"
          >
            Sign up
          </Button>
        </form>
      </div>
    </div>
  );
};

export default Signup;
