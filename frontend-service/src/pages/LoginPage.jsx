// src/pages/LoginPage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('/api/auth/login', { email, password });
      login(response.data.access_token);
      navigate('/dashboard'); // Navigate to dashboard on success
    } catch (error) {
      console.error('Login failed:', error);
      alert('Login failed. Please check your credentials.');
    }
  };

  return (
    <div>
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
        <button type="submit">Log In</button>
      </form>
      <p>Don't have an account? <a onClick={() => navigate('/register')}>Register</a></p>
    </div>
  );
};

export default LoginPage;