# Run the app

## Set environment variables

Create a copy of the `env.sample` file in the `backend` directory and rename it `.env`.

Open a terminal, and from any directory, run the following commands:

```
brew install postgresql@17
brew services start postgresql@17
psql postgres
```

Then run these commands:
```
CREATE DATABASE hercell;
\c hercell
\q
```

Now, set the `PG_URL` variable in the `.env` file:

```
PG_URL=postgresql://YOUR-MACOS-USERNAME@localhost:5432/hercell
```

In the terminal, generate a secure session secret by running:

```
openssl rand -base64 64
```

Now, set the `SESSION_SECRET` variable:

```
SESSION_SECRET=secure-session-secret-you-generated
```

For development purposes, you can use your personal Google account to populate the email-related environment variables. However, `EMAIL_PASSWORD` is not the typical password you would use to log into your email. You'll have to create an "app password" for your Google account (look up how to do this). Then, set these variables:

```
EMAIL_USER=your-google-email
EMAIL_PASSWORD=app-password-you-created
```

Now, create a copy of the `env.sample` file in the `frontend` directory and rename it `.env`. The one environment variable here is already provided.

## Install packages

From the `backend` directory, run the command `npm install`.

From the `frontend` directory, run the command `npm install`.

## Run the backend and frontend

Open a terminal. From the `backend` directory, run the command `npm run dev`.

Open another terminal. From the `frontend` directory, run the command `npm start`. The web app should automatically open on your computer.