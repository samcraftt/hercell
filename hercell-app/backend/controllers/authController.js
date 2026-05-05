const nodemailer = require('../config/nodemailer');
const Token = require('../models/Token');
const User = require('../models/User');

// Similar to authMiddleware, but for the frontend to query the current auth state
const checkAuth = async (req, res) => {
  try {
    if (!req.session.userId) return res.end();
    const user = await User.findById(req.session.userId);
    if (!user || !user.verified) return res.end();
    res.json({ user });
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: 'Error checking authentication' });
  }
};

const login = async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findByEmail(email);
    if (!user) return res.status(400).json({ error: 'There is no user with this email.' });
    const isCorrectPassword = await User.validatePassword(user.hashedPassword, password);
    if (!isCorrectPassword) return res.status(400).json({ error: 'The password you entered is incorrect.' });
    if (!user.verified) {
      const token = await Token.create(user.id);
      await nodemailer.sendVerificationEmail(email, token, user.id);
      return res.status(400).json({ error: 'Please check your email for verification.' });
    }
    req.session.userId = user.id;
    res.end();
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: 'Error logging in' });
  }
};

const logout = async (req, res) => {
  try {
    req.session.destroy((err) => {
      if (err) return res.status(500).json({ error: 'Error logging out' });
      res.clearCookie('sessionId');
      res.end();
    });
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: 'Error logging out' });
  }
};

const resetPassword = async (req, res) => {
  try {
    User.resetPassword(req.session.userId, req.body.password);
    res.end();
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: 'Error updating password, please try again.' });
  }
};

const sendResetPasswordEmail = async (req, res) => {
  try {
    const { email } = req.body;
    const user = await User.findByEmail(email);
    if (!user) return res.status(400).json({ error: 'There is no account with this email, please sign up.' });
    const token = await Token.create(user.id);
    await nodemailer.sendResetPasswordEmail(email, token, user.id);
    res.end();
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: 'Failed to reset password, please double check the email you entered.' });
  }
}

const signup = async (req, res) => {
  try {
    const { email, firstName, lastName, password } = req.body;
    const existingUser = await User.findByEmail(email);
    if (existingUser) return res.status(400).json({ error: 'An account with this email already exists, please log in.' });
    const user = await User.create({ email, firstName, lastName, password });
    const token = await Token.create(user.id);
    await nodemailer.sendVerificationEmail(email, token, user.id);
    res.end();
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: 'Error creating user' });
  }
};

const verifyEmail = async (req, res) => {
  try {
    const { token, userId } = req.body;
    const isValid = await Token.validate(userId, token);
    if (!isValid) return res.status(400).json({ error: 'Expired token, please try logging in again.' });
    const user = await User.verify(userId);
    if (!user) return res.status(400).json({ error: 'User not found, please try logging in again.' });
    req.session.userId = user.id;
    res.end();
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: 'Error verifying email, please try logging in again.' });
  }
};

module.exports = {
  checkAuth,
  login,
  logout,
  resetPassword,
  sendResetPasswordEmail,
  signup,
  verifyEmail
};
