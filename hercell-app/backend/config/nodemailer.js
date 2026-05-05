const nodemailer = require('nodemailer');
require('dotenv').config();

// Create mail transporter for gmail
const transporter = nodemailer.createTransport({
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASSWORD
  },
  service: 'gmail'
});

const sendResetPasswordEmail = async (email, token, userId) => {
  const newPasswordUrl = `${process.env.FRONTEND_URL}/reset-password?token=${token}&userId=${userId}`;
  const mailOptions = {
    from: process.env.EMAIL_USER,
    to: email,
    subject: 'Reset your password',
    html: `
      <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; color: #333;">
        <h1 style="color: #2563eb; font-size: 24px; margin-bottom: 20px; text-align: center;">Reset your password</h1>
        <p style="font-size: 16px; line-height: 1.5; margin-bottom: 25px; text-align: center;">
          Please click the button below to reset your password.
        </p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="${newPasswordUrl}" 
             style="background-color: #2563eb; 
                    color: white; 
                    padding: 12px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    font-weight: bold;
                    display: inline-block;">
            Reset password
          </a>
        </div>
        <p style="font-size: 14px; color: #666; margin-top: 25px;">
          If the button above doesn't work, you can copy and paste this link into your browser:
          <br>
          <span style="color: #2563eb; word-break: break-all;">${newPasswordUrl}</span>
        </p>
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666;">
          <p style="margin-bottom: 10px;">This link will expire in 1 hour for security reasons.</p>
          <p style="margin: 0;">If you didn't request to reset your password, you can safely ignore this email.</p>
        </div>
      </div>
    `,
  };
  await transporter.sendMail(mailOptions);
};

const sendVerificationEmail = async (email, token, userId) => {
  const verificationUrl = `${process.env.FRONTEND_URL}/verify-email?token=${token}&userId=${userId}`;
  const mailOptions = {
    from: process.env.EMAIL_USER,
    to: email,
    subject: 'Verify your email',
    html: `
      <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; color: #333;">
        <h1 style="color: #2563eb; font-size: 24px; margin-bottom: 20px; text-align: center;">Thank you for signing up!</h1>
        <p style="font-size: 16px; line-height: 1.5; margin-bottom: 25px; text-align: center;">
          Please click the button below to verify your email address.
        </p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="${verificationUrl}" 
             style="background-color: #2563eb; 
                    color: white; 
                    padding: 12px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    font-weight: bold;
                    display: inline-block;">
            Verify email
          </a>
        </div>
        <p style="font-size: 14px; color: #666; margin-top: 25px;">
          If the button above doesn't work, you can copy and paste this link into your browser:
          <br>
          <span style="color: #2563eb; word-break: break-all;">${verificationUrl}</span>
        </p>
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666;">
          <p style="margin-bottom: 10px;">This link will expire in 1 hour for security reasons.</p>
          <p style="margin: 0;">If you didn't request this verification, you can safely ignore this email.</p>
        </div>
      </div>
    `,
  };
  await transporter.sendMail(mailOptions);
};

module.exports = {
  sendResetPasswordEmail,
  sendVerificationEmail
};
