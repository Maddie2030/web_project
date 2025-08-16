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
  const [selectedBlockId, setSelectedBlockId] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [outputUrl, setOutputUrl] = useState(null);
  const [error, setError] = useState(null);
  const [blockIdCounter, setBlockIdCounter] = useState(1);

  const canvasElRef = useRef(null);
  const fabricRef = useRef(null);
  const objMapRef = useRef({});

  const generateBlockId = () => {
    const id = `block_${Date.now()}_${blockIdCounter}`;
    setBlockIdCounter(prev => prev + 1);
    return id;
  };

  const addNewTextBlock = (type = 'TITLE') => {
    const blockId = generateBlockId();
    const baseY = type === 'TITLE' ? 50 : 150;
    const existingCount = Object.keys(blocks).filter(id => blocks[id].type === type).length;
    
    const newBlock = {
      id: blockId,
      type: type,
      user_text: type === 'TITLE' ? 'Enter Title' : 'Enter Details',
      x: 50 + (existingCount * 20),
      y: baseY + (existingCount * 80),
      width: 200,
      height: 50,
      font_size: type === 'TITLE' ? 24 : 16,
      color: type === 'TITLE' ? '#000000' : '#333333',
      font_path: '',
      bold: type === 'TITLE' ? true : false,
      italic: false,
      max_width: 300,
    };

    setBlocks(prev => ({
      ...prev,
      [blockId]: newBlock
    }));
    
    setSelectedBlockId(blockId);
  };

  const removeTextBlock = (blockId) => {
    setBlocks(prev => {
      const newBlocks = { ...prev };
      delete newBlocks[blockId];
      return newBlocks;
    });
    
    const canvas = fabricRef.current;
    if (canvas && objMapRef.current[blockId]) {
      canvas.remove(objMapRef.current[blockId]);
      delete objMapRef.current[blockId];
      canvas.renderAll();
    }
    
    if (selectedBlockId === blockId) {
      setSelectedBlockId(null);
    }
  };

  const updateBlock = (blockId, updates) => {
    setBlocks(prev => ({
      ...prev,
      [blockId]: { ...prev[blockId], ...updates }
    }));
  };

  useEffect(() => {
    if (!token || !templateId) return;

    const fetchTemplate = async () => {
      try {
        const { data } = await axios.get(`${API_BASE}/api/v1/templates/${templateId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setTemplate(data);

        const init = {};
        data.text_blocks?.forEach((b, index) => {
          const blockId = `template_${index}`;
          init[blockId] = {
            id: blockId,
            type: 'TEMPLATE',
            user_text: b.default_text || b.title || '',
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

  useEffect(() => {
    if (!template || !canvasElRef.current) return;

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
        canvas.renderAll();
        
      } catch (err) {
        console.error('Failed to load background image:', err);
      }
    };

    // ✅ UPDATED: Event handler that properly handles textbox resizing
    const syncToState = (e) => {
      const obj = e.target;
      if (!obj || !obj.blockId) return;

      const blockId = obj.blockId;
      
      // ✅ Handle horizontal scaling only - let height adjust automatically
      if (obj.scaleX !== 1) {
        const newWidth = Math.max(50, Math.round((obj.width ?? 0) * obj.scaleX));
        obj.set({
          width: newWidth,
          scaleX: 1,
          scaleY: 1, // Reset Y scale to prevent distortion
        });
        
        updateBlock(blockId, {
          width: newWidth,
        });
      }

      const nx = clamp(Math.round(obj.left ?? 0), 0, CANVAS_W - (obj.width ?? 0));
      const ny = clamp(Math.round(obj.top ?? 0), 0, CANVAS_H - 200);
      obj.set({ left: nx, top: ny });

      updateBlock(blockId, {
        x: nx,
        y: ny,
        user_text: obj.text || '',
        height: obj.height, // Update height based on text wrapping
      });
    };
    
    const updateSelectedBlock = (e) => {
      const activeObject = e.target;
      if (activeObject && activeObject.blockId) {
        setSelectedBlockId(activeObject.blockId);
      } else {
        setSelectedBlockId(null);
      }
    };

    canvas.on('object:modified', syncToState);
    canvas.on('text:changed', syncToState);
    canvas.on('selection:created', updateSelectedBlock);
    canvas.on('selection:updated', updateSelectedBlock);
    canvas.on('selection:cleared', () => setSelectedBlockId(null));

    loadBackgroundAndObjects();

    return () => {
      canvas.off('object:modified', syncToState);
      canvas.off('text:changed', syncToState);
      canvas.off('selection:created', updateSelectedBlock);
      canvas.off('selection:updated', updateSelectedBlock);
      canvas.off('selection:cleared', () => setSelectedBlockId(null));
      canvas.dispose();
      fabricRef.current = null;
      objMapRef.current = {};
    };
  }, [template, API_BASE]);

  // ✅ UPDATED: Sync blocks to canvas with proper textbox configuration
  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;

    Object.values(blocks).forEach((block) => {
      if (!block.id) return;
      
      let obj = objMapRef.current[block.id];
      
      if (!obj) {
        // ✅ Create new Fabric Textbox with flexible resizing
        obj = new Textbox(block.user_text, {
          left: block.x,
          top: block.y,
          width: block.width,
          fontSize: block.font_size,
          fill: block.color,
          fontWeight: block.bold ? '700' : '400',
          fontStyle: block.italic ? 'italic' : 'normal',
          editable: true,
          
          // ✅ KEY PROPERTIES for flexible resizing:
          lockUniScaling: false,    // Allow non-uniform scaling
          lockScalingY: true,       // Lock vertical scaling to prevent distortion
          lockRotation: true,       // Disable rotation
          lockSkewingX: true,       // Disable skewing
          lockSkewingY: true,       // Disable skewing
          
          transparentCorners: false,
          cornerStyle: 'circle',
          borderScaleFactor: 1,
          objectCaching: false,
          
          // ✅ Text wrapping properties:
          textAlign: 'left',
          lineHeight: 1.2,
        });
        
        // Add unique identifier to Fabric object
        obj.blockId = block.id;
        obj.blockType = block.type;
        
        canvas.add(obj);
        objMapRef.current[block.id] = obj;
      } else {
        // Update existing Fabric object
        obj.set({
          left: block.x,
          top: block.y,
          width: block.width,
          fontSize: block.font_size,
          fill: block.color,
          fontWeight: block.bold ? '700' : '400',
          fontStyle: block.italic ? 'italic' : 'normal',
          text: block.user_text,
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
      const text_data = Object.values(blocks).map((block) => ({
        title: block.id,
        user_text: block.user_text,
        x: block.x,
        y: block.y,
        width: block.width,
        height: block.height,
        font_size: block.font_size,
        color: block.color,
        font_path: block.font_path || null,
        bold: block.bold,
        italic: block.italic,
        max_width: block.max_width,
        type: block.type,
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

  const selectedBlock = selectedBlockId ? blocks[selectedBlockId] : null;

  return (
    <div style={{ padding: '2rem', display: 'grid', gridTemplateColumns: '380px 1fr', gap: '1.5rem' }}>
      {/* Controls */}
      <div>
        <h2 style={{ marginTop: 0 }}>Customize: {template.name}</h2>

        {/* Add Text Block Buttons */}
        <div style={{ marginBottom: '1rem', display: 'flex', gap: '8px' }}>
          <button 
            onClick={() => addNewTextBlock('TITLE')} 
            style={{ 
              padding: '8px 12px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              flex: 1
            }}
          >
            + Add Title
          </button>
          <button 
            onClick={() => addNewTextBlock('DETAILS')} 
            style={{ 
              padding: '8px 12px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              flex: 1
            }}
          >
            + Add Details
          </button>
        </div>

        {/* Block List */}
        <div style={{ marginBottom: '1rem', maxHeight: '200px', overflowY: 'auto' }}>
          <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>Text Blocks:</h3>
          {Object.values(blocks).map((block) => (
            <div 
              key={block.id} 
              onClick={() => setSelectedBlockId(block.id)}
              style={{ 
                padding: '8px', 
                marginBottom: '4px',
                backgroundColor: selectedBlockId === block.id ? '#e3f2fd' : '#f5f5f5',
                border: selectedBlockId === block.id ? '1px solid #2196f3' : '1px solid #ddd',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: '12px' }}>
                  {block.type} 
                  {selectedBlockId === block.id && ' (Selected)'}
                </div>
                <div style={{ fontSize: '11px', opacity: 0.7 }}>
                  {block.user_text.substring(0, 20)}{block.user_text.length > 20 ? '...' : ''}
                </div>
              </div>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  removeTextBlock(block.id);
                }}
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  color: '#ff4444', 
                  cursor: 'pointer', 
                  fontSize: '16px',
                  padding: '0 4px'
                }}
              >
                ×
              </button>
            </div>
          ))}
        </div>

        {/* Selected Block Editor */}
        {selectedBlock && (
          <div style={{ border: '1px solid #ddd', borderRadius: '4px', padding: '12px', marginBottom: '1rem' }}>
            <h3 style={{ marginTop: 0, fontSize: '16px' }}>
              Edit {selectedBlock.type} Block
            </h3>
            
            <div style={{ marginBottom: '8px' }}>
              <label style={{ fontSize: '12px', display: 'block', marginBottom: '4px' }}>Text:</label>
              <textarea
                value={selectedBlock.user_text}
                onChange={(e) => updateBlock(selectedBlock.id, { user_text: e.target.value })}
                style={{ width: '100%', padding: '8px', minHeight: '60px', resize: 'vertical' }}
                placeholder={`Enter ${selectedBlock.type.toLowerCase()}`}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
              <div>
                <label style={{ fontSize: '12px', display: 'block', marginBottom: '4px' }}>Size:</label>
                <input
                  type="number"
                  min={6}
                  value={selectedBlock.font_size}
                  onChange={(e) => updateBlock(selectedBlock.id, { font_size: parseInt(e.target.value) || selectedBlock.font_size })}
                  style={{ width: '100%', padding: '4px' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '12px', display: 'block', marginBottom: '4px' }}>Color:</label>
                <input
                  type="color"
                  value={selectedBlock.color}
                  onChange={(e) => updateBlock(selectedBlock.id, { color: e.target.value })}
                  style={{ width: '100%', height: '32px' }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '8px' }}>
              <label style={{ fontSize: '12px', display: 'block', marginBottom: '4px' }}>Font:</label>
              <select
                value={selectedBlock.font_path || ''}
                onChange={(e) => updateBlock(selectedBlock.id, { font_path: e.target.value || null })}
                style={{ width: '100%', padding: '4px' }}
              >
                {defaultFonts.map((f) => (
                  <option key={f.label} value={f.value}>{f.label}</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <label style={{ fontSize: '12px', display: 'flex', alignItems: 'center' }}>
                <input
                  type="checkbox"
                  checked={selectedBlock.bold}
                  onChange={(e) => updateBlock(selectedBlock.id, { bold: e.target.checked })}
                  style={{ marginRight: '4px' }}
                />
                Bold
              </label>
              <label style={{ fontSize: '12px', display: 'flex', alignItems: 'center' }}>
                <input
                  type="checkbox"
                  checked={selectedBlock.italic}
                  onChange={(e) => updateBlock(selectedBlock.id, { italic: e.target.checked })}
                  style={{ marginRight: '4px' }}
                />
                Italic
              </label>
            </div>

            <div style={{ fontSize: '11px', opacity: 0.7, marginTop: '8px' }}>
              Position: ({selectedBlock.x}, {selectedBlock.y}) • Size: {selectedBlock.width}×{selectedBlock.height}
            </div>
          </div>
        )}

        <button onClick={handleGenerate} disabled={isGenerating} style={{ padding: '8px 14px', width: '100%' }}>
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
