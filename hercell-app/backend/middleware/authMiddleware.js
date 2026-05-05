const User = require('../models/User');

// Similar to checkAuth, but to protect routes that require authentication
const authMiddleware = async (req, res, next) => {
  try {
    if (!req.session.userId) return res.status(400).json({ error: 'Authentication required' });
    const user = await User.findById(req.session.userId);
    if (!user) return res.status(400).json({ error: 'User not found' });
    if (!user.verified) return res.status(400).json({ error: 'Email not verified' });
    req.user = user;
    next();
  } catch (error) {
    console.log(error);
    res.status(400).json({ error: 'Authentication failed' });
  }
};

module.exports = authMiddleware;
