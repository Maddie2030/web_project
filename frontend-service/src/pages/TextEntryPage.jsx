// src/pages/TextEntryPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const TextEntryPage = () => {
  const { templateId } = useParams();
  const [template, setTemplate] = useState(null);
  const [textInputs, setTextInputs] = useState({});
  const token = useAuthStore((state) => state.token);
  const navigate = useNavigate();

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

  useEffect(() => {
    const fetchTemplate = async () => {
      try {
        const response = await axios.get(`/api/v1/templates/${templateId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setTemplate(response.data);
      } catch (error) {
        console.error('Failed to fetch template:', error);
      }
    };

    if (token && templateId) {
      fetchTemplate();
    }
  }, [token, templateId]);

  const handleTextChange = (blockId, value) => {
    setTextInputs((prev) => ({
      ...prev,
      [blockId]: value,
    }));
  };

  if (!template) {
    return <div>Loading...</div>;
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h2>Text Entry for {template.name}</h2>
      <div style={{ display: 'flex', gap: '2rem' }}>
        {/* Left side: Input Form */}
        <div style={{ flex: 1, border: '1px solid #ccc', padding: '1rem' }}>
          <h3>Enter Your Text</h3>
          {template.text_blocks.map((block) => (
            <div key={block.id} style={{ marginBottom: '1rem' }}>
              <label htmlFor={block.id}>{block.name}:</label>
              <input
                id={block.id}
                type="text"
                value={textInputs[block.id] || ''}
                onChange={(e) => handleTextChange(block.id, e.target.value)}
                style={{ width: '100%', padding: '0.5rem' }}
              />
            </div>
          ))}
          <button style={{ padding: '0.5rem 1rem' }}>Generate Image</button>
        </div>

        {/* Right side: Live Preview */}
        <div
          style={{
            flex: 1,
            position: 'relative',
            width: '715px',
            height: '1144px',
            border: '1px solid black',
            // aspectRatio: '3 / 2', // Adjust to match your image aspect ratio
            // backgroundImage: `url(${template.image_path})`,
            backgroundImage: `url(${API_BASE}${template.image_path})`,
            backgroundSize: 'contain',
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'center',
          }}
        >
          {template.text_blocks.map((block) => (
            <div
              key={block.id}
              style={{
                position: 'absolute',
                left: `${block.x}px`,
                top: `${block.y}px`,
                fontSize: `${block.font_size}px`,
                color: block.color,
                fontFamily: block.font_family,
              }}
            >
              {textInputs[block.id]}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TextEntryPage;