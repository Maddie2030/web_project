// frontend-service/src/pages/TextEntryPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const TextEntryPage = () => {
  const { templateId } = useParams();
  const [template, setTemplate] = useState(null);
  const [textInputs, setTextInputs] = useState({});
  // New state variables for handling the rendering job
  const [isGenerating, setIsGenerating] = useState(false);
  const [outputUrl, setOutputUrl] = useState(null);
  const [error, setError] = useState(null);

  const token = useAuthStore((state) => state.token);
  const navigate = useNavigate();

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8003';

  useEffect(() => {
    const fetchTemplate = async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/v1/templates/${templateId}`, {
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
  }, [token, templateId, API_BASE]);

  const handleTextChange = (blockId, value) => {
    setTextInputs((prev) => ({
      ...prev,
      [blockId]: value,
    }));
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setOutputUrl(null);

    try {
      // --- UPDATE START ---
      // Transform the textInputs object into a list of objects as expected by the backend
      const textDataForBackend = Object.values(textInputs).map(text => ({
        user_text: text,
      }));
      // --- UPDATE END ---

      // 1. Send text data to the render service
      const response = await axios.post(`${API_BASE}/api/v1/render/generate-image`, {
        template_id: templateId,
        text_data: textDataForBackend, // Use the new, correctly formatted data
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('Image generation job started successfully:', response.data);

      const { job_id } = response.data;

      // 2. Start polling for job status
      const checkStatus = setInterval(async () => {
        try {
          const statusResponse = await axios.get(`${API_BASE}/api/v1/render/status/${job_id}`, {
            headers: { Authorization: `Bearer ${token}` },
          });

          if (statusResponse.data.status === 'completed') {
            clearInterval(checkStatus);
            setOutputUrl(statusResponse.data.output_url);
            setIsGenerating(false);
          } else if (statusResponse.data.status === 'failed') {
            clearInterval(checkStatus);
            setError('Image generation failed.');
            setIsGenerating(false);
          }
        } catch (statusError) {
          clearInterval(checkStatus);
          setError('Failed to check job status.');
          setIsGenerating(false);
          console.error(statusError);
        }
      }, 3000); // Poll every 3 seconds

    } catch (generateError) {
      console.error('Generation request failed:', generateError);
      setError('Failed to start image generation.');
      setIsGenerating(false);
    }
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
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            style={{ padding: '0.5rem 1rem' }}
          >
            {isGenerating ? 'Generating...' : 'Generate Image'}
          </button>
          
          {error && <p style={{ color: 'red' }}>{error}</p>}
        </div>

        {/* Right side: Live Preview and Final Output */}
        <div style={{ flex: 1 }}>
          {/* Display live preview while no output is available */}
          {!outputUrl && (
            <div
              style={{
                position: 'relative',
                width: '715px',
                height: '1144px',
                border: '1px solid black',
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
          )}

          {/* Display final generated image and download link */}
          {outputUrl && (
            <div>
              <h3>Generated Image</h3>
              <img src={`${API_BASE}${outputUrl}`} alt="Generated Output" style={{ maxWidth: '100%' }} />
              <a href={`${API_BASE}${outputUrl}`} download>
                <button style={{ marginTop: '1rem' }}>Download Image</button>
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TextEntryPage;