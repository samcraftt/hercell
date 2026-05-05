import { Link } from 'react-router-dom';

const NotFound = () => {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="flex flex-col items-center space-y-4">
        <h2 className="text-2xl font-bold tracking-tight text-gray-900">
          The page you're looking for doesn't exist.
        </h2>
        <Link
          className="font-medium text-blue-600 hover:text-blue-500"
          to="/"
        >
          Back to home
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
