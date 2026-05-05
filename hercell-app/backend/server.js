const authRoutes = require('./routes/authRoutes');
const basicAuth = require('express-basic-auth');
const cors = require('cors');
const express = require('express');
const her2Routes = require('./routes/her2Routes');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const redisClient = require('./config/redis');
const { RedisStore } = require('connect-redis');
const session = require('express-session');
require('dotenv').config();

const app = express();

// Trust first proxy
app.set('trust proxy', 1);

// Password protect the staging site
if (process.env.ENVIRONMENT === 'staging') {
  app.use(basicAuth({
    users: { 
      [process.env.STAGING_USERNAME]: process.env.STAGING_PASSWORD
    },
    challenge: true,
    realm: 'Staging site'
  }));
}

// Security
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL,
  credentials: true
}));

// Session
const redisStore = new RedisStore({
  client: redisClient,
  prefix: "session:"
});
const isDeployedEnvironment = process.env.ENVIRONMENT === 'production' || process.env.ENVIRONMENT === 'staging';
app.use(session({
  cookie: {
    httpOnly: true,
    maxAge: 7 * 24 * 60 * 60 * 1000,
    sameSite: isDeployedEnvironment ? 'none' : 'lax',
    secure: isDeployedEnvironment
  },
  name: 'sessionId',
  resave: false,
  saveUninitialized: false,
  secret: process.env.SESSION_SECRET,
  store: redisStore
}));

// Limit IPs to 2000 requests per 15 min
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 2000
});
app.use('/', limiter);

// To parse request parameters
app.use(express.json());

// Routes
app.use('/auth', authRoutes);
app.use('/her2', her2Routes);

// To handle image upload
app.use((error, _, res, next) => {
  if (error?.name === 'MulterError' && error.code === 'LIMIT_FILE_SIZE') {
    return res.status(400).json({ error: 'Slide file must be 10MB or smaller.' });
  }
  if (error?.name === 'MulterError') {
    return res.status(400).json({ error: 'Invalid slide upload.' });
  }
  next(error);
});

app.listen(process.env.PORT || '8000');
