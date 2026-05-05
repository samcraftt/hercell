const passwordHelper = {
    defaultSecurity: {
        hasEightChars: false,
        hasUpperCase: false,
        hasLowerCase: false,
        hasNumber: false,
        hasSpecialChar: false,
        passwordsMatch: false
    },

    getSecurity: (password, confirmPassword) => {
        const results = {};
        Object.keys(passwordHelper.requirements).forEach(requirement => {
            if (passwordHelper.requirements[requirement].regex) results[requirement] = passwordHelper.requirements[requirement].regex.test(password);
        });
        results.passwordsMatch = password === confirmPassword;
        return results;
    },

    requirements: {
        hasEightChars: { regex: /.{8,}/, text: 'At least 8 characters' },
        hasUpperCase: { regex: /[A-Z]/, text: 'At least 1 uppercase letter' },
        hasLowerCase: { regex: /[a-z]/, text: 'At least 1 lowercase letter' },
        hasNumber: { regex: /[0-9]/, text: 'At least 1 number' },
        hasSpecialChar: { regex: /[!@#$%^&*(),.?":{}|<>]/, text: 'At least 1 special character' },
        passwordsMatch: { text: 'Passwords match'}
    },

    requirementsDisplay: (passwordSecurity) => {
        return (
            <div className="mt-2 text-sm">
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(passwordHelper.requirements).map(([key, { text }]) => (
                  <div key={key} className="flex items-center space-x-2">
                    <span className={`flex-shrink-0 h-5 w-5 rounded-full flex items-center justify-center ${
                      passwordSecurity[key] ? 'bg-green-100 text-green-500' : 'bg-gray-100 text-gray-400'
                    }`}>
                      {passwordSecurity[key] ? '✓' : '○'}
                    </span>
                    <span className={`${passwordSecurity[key] ? 'text-green-600' : 'text-gray-600'} text-xs`}>
                      {text}
                    </span>
                  </div>
                ))}
              </div>
            </div>
        );
    }
};

export default passwordHelper;
