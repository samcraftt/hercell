import { Toaster as HotToaster } from 'react-hot-toast';

const Toaster = () => {
  return (
    <HotToaster
      position="top-right"
      reverseOrder={false}
      toastOptions={{
        className: '',
        duration: 5000,
        error: {
          duration: 10000,
          style: {
            background: '#fee2e2',
            border: '1px solid #ef4444',
            color: '#991b1b',
          },
        },
        success: {
          style: {
            background: '#dcfce7',
            border: '1px solid #22c55e',
            color: '#166534',
          },
        },
        style: {
          borderRadius: '0.375rem',
          maxWidth: '500px',
          padding: '1rem',
        },
      }}
    />
  );
};

export default Toaster;
