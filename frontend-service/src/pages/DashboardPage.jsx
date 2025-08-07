import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const DashboardPage = () => {
  const [templates, setTemplates] = useState([]);
  const token = useAuthStore((state) => state.token);
  const navigate = useNavigate();

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await axios.get('/api/v1/templates/templates', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setTemplates(response.data);
      } catch (error) {
        console.error('Failed to fetch templates:', error);
      }
    };

    if (token) {
      fetchTemplates();
    }
  }, [token]);

  const handleSelectTemplate = (templateId) => {
    navigate(`/text-entry/${templateId}`);
  };

  return (
    <div>
      <h2>Template Dashboard</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        {templates.length > 0 ? (
          templates.map((template) => (
            <div key={template.id} style={{ border: '1px solid #ccc', padding: '10px' }}>
              <h3>{template.name}</h3>
              <img
                src={`${API_BASE}${template.image_path}`}
                alt={template.name}
                style={{ width: '100%', objectFit: 'cover' }}
              />
              <button onClick={() => handleSelectTemplate(template.id)}>Select</button>
            </div>
          ))
        ) : (
          <p>Loading templates...</p>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
