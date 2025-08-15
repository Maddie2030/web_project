import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { Canvas, FabricImage, Textbox } from 'fabric';

const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

const defaultFonts = [
  { label: 'DejaVu Sans', value: '/usr/share/fonts/dejavu/DejaVuSans.ttf' },
  { label: 'Arial (system)', value: '' },
  { label: 'Roboto', value: '' },
  { label: 'Open Sans', value: '' },
  { label: 'Lato', value: '' },
  { label: 'Montserrat', value: '' },
  { label: 'Verdana', value: '' },
  { label: 'Georgia', value: '' },
  { label: 'Courier New', value: '' },
  { label: 'Times New Roman', value: '' },
  { label: 'Trebuchet MS', value: '' },
];

const CANVAS_W = 715;
const CANVAS_H = 1144;

const TextEntryPage = () => {
  const { templateId } = useParams();
  const token = useAuthStore((s) => s.token);
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8003';

  const [template, setTemplate] = useState(null);
  const [blocks, setBlocks] = useState({});
  const [selectedTitle, setSelectedTitle] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [outputUrl, setOutputUrl] = useState(null);
  const [error, setError] = useState(null);

  const canvasElRef = useRef(null);
  const fabricRef = useRef(null);
  const objMapRef = useRef({});

  // ✅ FIXED: Generate truly unique titles
  const generateUniqueTitle = (baseTitle = 'NewBlock') => {
    let counter = 1;
    let newTitle = `${baseTitle}${counter}`;
    
    // Keep incrementing until we find a unique title
    while (blocks[newTitle]) {
      counter++;
      newTitle = `${baseTitle}${counter}`;
    }
    
    return newTitle;
  };

  const addNewTextBlock = () => {
    const newTitle = generateUniqueTitle('NewBlock');
    
    setBlocks(prev => ({
      ...prev,
      [newTitle]: {
        title: newTitle,
        user_text: '',
        x: 10 + (Object.keys(prev).length * 10),
        y: 10 + (Object.keys(prev).length * 40),
        width: 200,
        height: 50,
        font_size: 14,
        color: '#000000',
        font_path: '',
        bold: false,
        italic: false,
        max_width: 200,
      },
    }));
  };

  const removeTextBlock = (titleToRemove) => {
    setBlocks(prev => {
      const newBlocks = { ...prev };
      delete newBlocks[titleToRemove];
      return newBlocks;
    });
    
    const canvas = fabricRef.current;
    if (canvas && objMapRef.current[titleToRemove]) {
      canvas.remove(objMapRef.current[titleToRemove]);
      delete objMapRef.current[titleToRemove];
      canvas.renderAll();
    }
  };

  // Fetch template and initialize blocks state
  useEffect(() => {
    if (!token || !templateId) return;

    const fetchTemplate = async () => {
      try {
        const { data } = await axios.get(`${API_BASE}/api/v1/templates/${templateId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setTemplate(data);

        const init = {};
        const usedTitles = new Set(); // Track used titles to avoid duplicates
        
        data.text_blocks.forEach((b, index) => {
          // ✅ FIXED: Ensure unique titles even from template data
          let title = b.title || `TemplateBlock${index + 1}`;
          
          // If title already exists, make it unique
          if (usedTitles.has(title)) {
            let counter = 1;
            while (usedTitles.has(`${title}_${counter}`)) {
              counter++;
            }
            title = `${title}_${counter}`;
          }
          
          usedTitles.add(title);
          
          init[title] = {
            title: title,
            user_text: b.default_text || '',
            x: b.x,
            y: b.y,
            width: b.width,
            height: b.height,
            font_size: b.font_size,
            color: b.color || '#000000',
            font_path: b.font_path || '',
            bold: !!b.bold,
            italic: !!b.italic,
            max_width: b.max_width || b.width,
          };
        });
        setBlocks(init);
      } catch (err) {
        console.error(err);
        setError('Failed to load template');
      }
    };

    fetchTemplate();
  }, [token, templateId, API_BASE]);

  // Initialize Fabric.js canvas and populate with objects
  useEffect(() => {
    if (!template || !canvasElRef.current || !Object.keys(blocks).length) return;

    if (fabricRef.current) {
      fabricRef.current.dispose();
      objMapRef.current = {};
    }

    const canvas = new Canvas(canvasElRef.current, {
      width: CANVAS_W,
      height: CANVAS_H,
      selection: true,
      backgroundColor: null,
      preserveObjectStacking: true,
    });
    fabricRef.current = canvas;

    const loadBackgroundAndObjects = async () => {
      const bgUrl = `${API_BASE}${template.image_path}`;
      
      try {
        const img = await FabricImage.fromURL(bgUrl, { crossOrigin: 'anonymous' });
        
        const scaleX = CANVAS_W / img.width;
        const scaleY = CANVAS_H / img.height;
        const scale = Math.min(scaleX, scaleY);
        img.scale(scale);
        
        img.set({
          left: (CANVAS_W - img.width * scale) / 2,
          top: (CANVAS_H - img.height * scale) / 2,
          originX: 'left',
          originY: 'top',
          selectable: false,
          evented: false,
        });
        
        canvas.backgroundImage = img;
        addTextBlocks();
        canvas.renderAll();
        
      } catch (err) {
        console.error('Failed to load background image:', err);
        addTextBlocks();
        canvas.renderAll();
      }
    };

    const addTextBlocks = () => {
      Object.values(blocks).forEach((b) => {
        if (!b.title) return;
        
        const tb = new Textbox(b.user_text || b.title, {
          left: b.x,
          top: b.y,
          width: b.width,
          fontSize: b.font_size,
          fill: b.color,
          fontWeight: b.bold ? '700' : '400',
          fontStyle: b.italic ? 'italic' : 'normal',
          editable: true,
          lockScalingFlip: true,
          transparentCorners: false,
          cornerStyle: 'circle',
          borderScaleFactor: 1,
          objectCaching: false,
        });

        canvas.add(tb);
        objMapRef.current[b.title] = tb;
      });
    };

    // Event handlers
    const syncToState = (e) => {
      const obj = e.target;
      if (!obj) return;
      const title = Object.keys(objMapRef.current).find((k) => objMapRef.current[k] === obj);
      if (!title) return;

      if (obj.scaleX !== 1 || obj.scaleY !== 1) {
        const newWidth = Math.max(20, Math.round((obj.width ?? 0) * obj.scaleX));
        const newFontSize = Math.max(6, Math.round((obj.fontSize ?? 12) * obj.scaleY));
        obj.set({
          width: newWidth,
          fontSize: newFontSize,
          scaleX: 1,
          scaleY: 1,
        });
      }

      const nx = clamp(Math.round(obj.left ?? 0), 0, CANVAS_W - (obj.width ?? 0));
      const ny = clamp(Math.round(obj.top ?? 0), 0, CANVAS_H - (obj.height ?? 0));
      obj.set({ left: nx, top: ny });

      setBlocks((prev) => ({
        ...prev,
        [title]: {
          ...prev[title],
          x: nx,
          y: ny,
          width: Math.round(obj.width ?? prev[title].width),
          font_size: Math.round(obj.fontSize ?? prev[title].font_size),
          user_text: obj.text || '',
        },
      }));
    };
    
    const updateSelectedTitle = (e) => {
      const activeObject = e.target;
      if (activeObject) {
        const title = Object.keys(objMapRef.current).find((k) => objMapRef.current[k] === activeObject);
        setSelectedTitle(title);
      } else {
        setSelectedTitle(null);
      }
    };

    canvas.on('object:modified', syncToState);
    canvas.on('text:changed', syncToState);
    canvas.on('selection:created', updateSelectedTitle);
    canvas.on('selection:updated', updateSelectedTitle);
    canvas.on('selection:cleared', updateSelectedTitle);

    loadBackgroundAndObjects();

    return () => {
      canvas.off('object:modified', syncToState);
      canvas.off('text:changed', syncToState);
      canvas.off('selection:created', updateSelectedTitle);
      canvas.off('selection:updated', updateSelectedTitle);
      canvas.off('selection:cleared', updateSelectedTitle);
      canvas.dispose();
      fabricRef.current = null;
      objMapRef.current = {};
    };
  }, [template, API_BASE]);

  // Sync React-side control edits back into Fabric objects AND create new ones
  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;

    Object.values(blocks).forEach((b) => {
      if (!b.title) return;
      
      let obj = objMapRef.current[b.title];
      
      if (!obj) {
        obj = new Textbox(b.user_text || b.title, {
          left: b.x,
          top: b.y,
          width: b.width,
          fontSize: b.font_size,
          fill: b.color,
          fontWeight: b.bold ? '700' : '400',
          fontStyle: b.italic ? 'italic' : 'normal',
          editable: true,
          lockScalingFlip: true,
          transparentCorners: false,
          cornerStyle: 'circle',
          borderScaleFactor: 1,
          objectCaching: false,
        });
        
        canvas.add(obj);
        objMapRef.current[b.title] = obj;
      } else {
        obj.set({
          left: b.x,
          top: b.y,
          width: b.width,
          fontSize: b.font_size,
          fill: b.color,
          fontWeight: b.bold ? '700' : '400',
          fontStyle: b.italic ? 'italic' : 'normal',
          text: b.user_text || b.title,
        });
      }
    });
    
    canvas.renderAll();
  }, [blocks]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setOutputUrl(null);
    try {
      const text_data = Object.values(blocks)
        .filter(b => b.title)
        .map((b) => ({
          title: b.title,
          user_text: b.user_text,
          x: b.x,
          y: b.y,
          width: b.width,
          height: b.height,
          font_size: b.font_size,
          color: b.color,
          font_path: b.font_path || null,
          bold: b.bold,
          italic: b.italic,
          max_width: b.max_width || b.width,
        }));

      const resp = await axios.post(
        `${API_BASE}/api/v1/render/generate-image`,
        { template_id: templateId, text_data },
        { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } }
      );

      if (resp.data?.image_url) {
        setOutputUrl(resp.data.image_url);
        setIsGenerating(false);
      } else if (resp.data?.job_id) {
        const jobId = resp.data.job_id;
        const timer = setInterval(async () => {
          try {
            const s = await axios.get(`${API_BASE}/api/v1/render/status/${jobId}`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            if (s.data.status === 'completed') {
              clearInterval(timer);
              setOutputUrl(s.data.output_url);
              setIsGenerating(false);
            } else if (s.data.status === 'failed') {
              clearInterval(timer);
              setError('Image generation failed.');
              setIsGenerating(false);
            }
          } catch {
            clearInterval(timer);
            setIsGenerating(false);
            setError('Failed to check job status.');
          }
        }, 2000);
      } else {
        setError('Unexpected response from render service.');
        setIsGenerating(false);
      }
    } catch (e) {
      console.error(e);
      setError('Failed to start image generation.');
      setIsGenerating(false);
    }
  };

  if (!template) return <div style={{ padding: '2rem' }}>Loading...</div>;

  return (
    <div style={{ padding: '2rem', display: 'grid', gridTemplateColumns: '380px 1fr', gap: '1.5rem' }}>
      {/* Controls */}
      <div>
        <h2 style={{ marginTop: 0 }}>Customize: {template.name}</h2>

        {Object.values(blocks).map((b) => (
          // ✅ FIXED: Use b.title as key since it's now guaranteed to be unique
          <div key={b.title} style={{ borderBottom: '1px solid #eee', paddingBottom: '0.75rem', marginBottom: '0.75rem', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <div style={{ fontWeight: 600 }}>{b.title || 'Untitled Block'}</div>
              {b.title && b.title.startsWith('NewBlock') && (
                <button 
                  onClick={() => removeTextBlock(b.title)}
                  style={{ 
                    background: 'none', 
                    border: 'none', 
                    color: '#ff4444', 
                    cursor: 'pointer', 
                    fontSize: '16px',
                    padding: '0 4px'
                  }}
                  title="Remove block"
                >
                  ×
                </button>
              )}
            </div>
            
            <input
              type="text"
              value={b.user_text || ''}
              onChange={(e) => setBlocks((prev) => ({ ...prev, [b.title]: { ...b, user_text: e.target.value } }))}
              style={{ width: '100%', padding: '8px', marginBottom: 8 }}
              placeholder={`Enter ${b.title || 'text'}`}
            />
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
              <label style={{ fontSize: 12 }}>Size</label>
              <input
                type="number"
                min={6}
                value={b.font_size || 14}
                onChange={(e) =>
                  setBlocks((prev) => ({
                    ...prev,
                    [b.title]: { ...b, font_size: parseInt(e.target.value) || b.font_size },
                  }))
                }
                style={{ width: 90 }}
              />
              <label style={{ fontSize: 12 }}>Color</label>
              <input
                type="color"
                value={b.color || '#000000'}
                onChange={(e) => setBlocks((prev) => ({ ...prev, [b.title]: { ...b, color: e.target.value } }))}
              />
              <label style={{ fontSize: 12 }}>Font</label>
              <select
                value={b.font_path || ''}
                onChange={(e) => setBlocks((prev) => ({ ...prev, [b.title]: { ...b, font_path: e.target.value || null } }))}
              >
                {defaultFonts.map((f) => (
                  <option key={f.label} value={f.value}>{f.label}</option>
                ))}
              </select>
              <label style={{ fontSize: 12 }}>
                <input
                  type="checkbox"
                  checked={!!b.bold}
                  onChange={(e) => setBlocks((prev) => ({ ...prev, [b.title]: { ...b, bold: e.target.checked } }))}
                />{' '}
                Bold
              </label>
              <label style={{ fontSize: 12 }}>
                <input
                  type="checkbox"
                  checked={!!b.italic}
                  onChange={(e) => setBlocks((prev) => ({ ...prev, [b.title]: { ...b, italic: e.target.checked } }))}
                />{' '}
                Italic
              </label>
            </div>
            <div style={{ fontSize: 12, opacity: 0.7 }}>
              Pos: ({b.x || 0}, {b.y || 0}) • Box: {b.width || 0}×{b.height || 0}
            </div>
          </div>
        ))}

        <button 
          onClick={addNewTextBlock} 
          style={{ 
            marginTop: '1rem', 
            padding: '8px 12px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            width: '100%'
          }}
        >
          + Add Text Block
        </button>

        <button onClick={handleGenerate} disabled={isGenerating} style={{ padding: '8px 14px', marginTop: '1rem', width: '100%' }}>
          {isGenerating ? 'Generating...' : 'Generate Image'}
        </button>
        {error && <p style={{ color: 'crimson', marginTop: 12 }}>{error}</p>}
      </div>

      {/* Canvas / Preview */}
      <div>
        {!outputUrl && (
          <div style={{ position: 'relative', width: CANVAS_W, height: CANVAS_H, border: '1px solid #000' }}>
            <canvas ref={canvasElRef} width={CANVAS_W} height={CANVAS_H} />
          </div>
        )}

        {outputUrl && (
          <div>
            <h3>Generated Image</h3>
            <img src={`${API_BASE}${outputUrl}`} alt="Generated Output" style={{ maxWidth: '100%' }} />
            <a href={`${API_BASE}${outputUrl}`} download>
              <button style={{ marginTop: 12 }}>Download Image</button>
            </a>
          </div>
        )}
      </div>
    </div>
  );
};

export default TextEntryPage;
