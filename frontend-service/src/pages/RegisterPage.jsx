//frontend-service/src/pages/RegisterPage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const RegisterPage = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      alert('Passwords do not match.');
      return;
    }
    try {
      await axios.post('/api/v1/auth/register', { username, email, password });
      alert('Registration successful! Please log in.');
      navigate('/login');
    } catch (error) {
      // Check for a specific error response from the server
      if (error.response) {
        if (error.response.status === 409) {
          alert('Registration failed: Username or email already exists.');
        } else if (error.response.status === 422) {
          alert('Registration failed: Please check your input fields and try again.');
          console.error('Validation Error:', error.response.data);
        } else {
          // Handle other types of server errors
          alert(`Registration failed with status: ${error.response.status}`);
          console.error('API Error:', error.response.data);
        }
      } else {
        // Handle network errors (e.g., connection refused)
        alert('Network Error: Could not connect to the server.');
        console.error('Network Error:', error.message);
      }
    }
  };

  return (
    <div>
      <h2>Register</h2>
      <form onSubmit={handleSubmit}>
        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" required />
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
        <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Confirm Password" required />
        <button type="submit">Register</button>
      </form>
      <p>Already have an account? <a onClick={() => navigate('/login')}>Log In</a></p>
    </div>
  );
};

export default RegisterPage;