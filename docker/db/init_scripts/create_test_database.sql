-- Create the test_app database
CREATE DATABASE test_app;

-- Create a test_user for the test_app database
CREATE USER test_user WITH PASSWORD 'test_password';

-- Grant all privileges on the test_app database to the test_user
GRANT ALL PRIVILEGES ON DATABASE test_app TO test_user;

-- Connect to the test_app database
\connect test_app

-- Grant all privileges on the public schema to test_user
GRANT ALL PRIVILEGES ON SCHEMA public TO test_user;