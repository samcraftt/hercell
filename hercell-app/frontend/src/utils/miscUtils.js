import toast from 'react-hot-toast';

export const showErrorMessage = (error, defaultMessage) => {
    const message = error.response?.data?.error || defaultMessage;
    toast.error(message);
};
