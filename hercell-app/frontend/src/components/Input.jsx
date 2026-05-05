const Input = ({
  className = '',
  error,
  id,
  label,
  name,
  onChange,
  placeholder = '',
  required,
  type = 'text',
  value,
}) => {
  const baseInputStyles = 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm';
  const errorInputStyles = 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500';
  return (
    <div className={className}>
      {label && (
        <label
          className="block text-sm font-medium text-gray-700"
          htmlFor={id}
        >
          {label}
        </label>
      )}
      <div className="mt-1">
        <input
          className={`${baseInputStyles} ${error ? errorInputStyles : ''}`}
          id={id}
          name={name}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          type={type}
          value={value}
        />
      </div>
      {error && (
        <p className="mt-2 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
};

export default Input;
