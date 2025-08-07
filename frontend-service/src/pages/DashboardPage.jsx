import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const DashboardPage = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const token = useAuthStore((state) => state.token);
  const navigate = useNavigate();

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

  // Use useEffect to fetch templates automatically when the component mounts
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/v1/templates/templates', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setTemplates(response.data);
      } catch (error) {
        console.error('Failed to fetch templates:', error);
      } finally {
        setLoading(false);
      }
    };

    if (token) { // Only fetch if a token exists
      fetchTemplates();
    }
  }, [token]); // The empty dependency array ensures this runs only once, on mount.

  const handleSelectTemplate = (templateId) => {
    navigate(`/text-entry/${templateId}`);
  };

  return (
    <div>
      <h2>Template Dashboard</h2>
      
      {/* The button is now for a manual refresh, if needed */}
      <button onClick={() => { /* You can add a manual refresh function here if you want */ }} disabled={loading}>
        {loading ? 'Loading...' : 'Templates are displayed automatically'}
      </button>

      <div style={{ marginTop: '20px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        {loading ? (
          <p>Loading templates...</p>
        ) : templates.length > 0 ? (
          templates.map((template) => (
            <div key={template._id} style={{ border: '1px solid #ccc', padding: '10px' }}>
              <h3>{template.name}</h3>
              <img
                src={`${API_BASE}${template.image_path}`}
                alt={template.name}
                style={{ width: '100%', objectFit: 'cover' }}
              />
              <button onClick={() => handleSelectTemplate(template._id)}>Select</button>
            </div>
          ))
        ) : (
          <p>No templates to display.</p>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;