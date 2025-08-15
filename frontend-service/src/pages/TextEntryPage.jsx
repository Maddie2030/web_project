import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { Canvas, FabricImage, Textbox } from 'fabric';

const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

const defaultFonts = [
  { label: 'DejaVu Sans', value: '/usr/share/fonts/dejavu/DejaVuSans.ttf' },
  { label: 'Arial (system)', value: '' },
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
        data.text_blocks.forEach((b) => {
          init[b.title] = {
            title: b.title,
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

    // Dispose of old canvas if it exists
    if (fabricRef.current) {
      fabricRef.current.dispose();
      objMapRef.current = {};
    }

    const canvas = new Canvas(canvasElRef.current, {
      width: CANVAS_W,
      height: CANVAS_H,
      selection: true,
      backgroundColor: null, // Transparent background
      preserveObjectStacking: true,
    });
    fabricRef.current = canvas;

    // ✅ Correct way to set background image in v6
    const loadBackgroundAndObjects = async () => {
      const bgUrl = `${API_BASE}${template.image_path}`;
      
      try {
        // Load the image
        const img = await FabricImage.fromURL(bgUrl, { crossOrigin: 'anonymous' });
        
        // Scale image to fit canvas
        const scaleX = CANVAS_W / img.width;
        const scaleY = CANVAS_H / img.height;
        const scale = Math.min(scaleX, scaleY);
        img.scale(scale);
        
        // Position the image
        img.set({
          left: (CANVAS_W - img.width * scale) / 2,
          top: (CANVAS_H - img.height * scale) / 2,
          originX: 'left',
          originY: 'top',
          selectable: false,
          evented: false,
        });
        
        // ✅ Set backgroundImage property directly (v6 way)
        canvas.backgroundImage = img;
        
        // Add text blocks after background is set
        addTextBlocks();
        
        // Render the canvas
        canvas.renderAll();
        
      } catch (err) {
        console.error('Failed to load background image:', err);
        // Add text blocks even if background fails
        addTextBlocks();
        canvas.renderAll();
      }
    };

    // Function to add text blocks
    const addTextBlocks = () => {
      Object.values(blocks).forEach((b) => {
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

      // Apply scaling to width/fontSize before updating state
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

      // Clamp move into canvas
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

    // Add event listeners
    canvas.on('object:modified', syncToState);
    canvas.on('text:changed', syncToState);
    canvas.on('selection:created', updateSelectedTitle);
    canvas.on('selection:updated', updateSelectedTitle);
    canvas.on('selection:cleared', updateSelectedTitle);

    // Load background and objects
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

  // Sync React-side control edits back into Fabric objects
  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;

    Object.values(blocks).forEach((b) => {
      const obj = objMapRef.current[b.title];
      if (!obj) return;
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
    });
    canvas.renderAll();
  }, [blocks]);




  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setOutputUrl(null);
    try {
      const text_data = Object.values(blocks).map((b) => ({
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

  if (!template) return <div style={{ padding: '2rem' }}>Loading…</div>;

  return (
    <div style={{ padding: '2rem', display: 'grid', gridTemplateColumns: '380px 1fr', gap: '1.5rem' }}>
      {/* Controls */}
      <div>
        <h2 style={{ marginTop: 0 }}>Customize: {template.name}</h2>

        {Object.values(blocks).map((b, index) => (
          <div key={b.title || index} style={{ borderBottom: '1px solid #eee', paddingBottom: '0.75rem', marginBottom: '0.75rem' }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>{b.title}</div>
            <input
              type="text"
              value={b.user_text}
              onChange={(e) => setBlocks((prev) => ({ ...prev, [b.title]: { ...b, user_text: e.target.value } }))}
              style={{ width: '100%', padding: '8px', marginBottom: 8 }}
              placeholder={`Enter ${b.title}`}
            />
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
              <label style={{ fontSize: 12 }}>Size</label>
              <input
                type="number"
                min={6}
                value={b.font_size}
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
                value={b.color}
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
              Pos: ({b.x}, {b.y}) • Box: {b.width}×{b.height}
            </div>
          </div>
        ))}

        <button onClick={handleGenerate} disabled={isGenerating} style={{ padding: '8px 14px' }}>
          {isGenerating ? 'Generating…' : 'Generate Image'}
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
