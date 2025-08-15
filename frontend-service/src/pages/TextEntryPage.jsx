// frontend-service/src/pages/TextEntryPage.jsx
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

const defaultFonts = [
  { label: 'DejaVu Sans', value: '/usr/share/fonts/dejavu/DejaVuSans.ttf' },
  { label: 'Arial (system)', value: '' }, // renderer will fallback if empty
];

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

  const stageRef = useRef(null);
  const contextMenuRef = useRef(null);
  const [menu, setMenu] = useState({ visible: false, x: 0, y: 0 });

  // Fetch template once
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

  // Mouse/drag state
  const dragState = useRef({ mode: null, startX: 0, startY: 0, origX: 0, origY: 0, origW: 0, origH: 0, origFS: 0 });

  const onBlockMouseDown = (e, title) => {
    e.stopPropagation();
    setSelectedTitle(title);
    const rect = stageRef.current.getBoundingClientRect();
    dragState.current = {
      mode: 'move',
      startX: e.clientX - rect.left,
      startY: e.clientY - rect.top,
      origX: blocks[title].x,
      origY: blocks[title].y,
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const onHandleMouseDown = (e, title) => {
    e.stopPropagation();
    setSelectedTitle(title);
    const rect = stageRef.current.getBoundingClientRect();
    const b = blocks[title];
    dragState.current = {
      mode: 'resize',
      startX: e.clientX - rect.left,
      startY: e.clientY - rect.top,
      origW: b.width,
      origH: b.height,
      origFS: b.font_size,
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const onMouseMove = (e) => {
    const rect = stageRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const { mode, startX, startY, origX, origY, origW, origH, origFS } = dragState.current;
    if (!mode || !selectedTitle) return;

    setBlocks((prev) => {
      const b = prev[selectedTitle];
      if (!b) return prev;

      if (mode === 'move') {
        const nx = clamp(origX + (x - startX), 0, rect.width - b.width);
        const ny = clamp(origY + (y - startY), 0, rect.height - b.height);
        return { ...prev, [selectedTitle]: { ...b, x: Math.round(nx), y: Math.round(ny) } };
      }

      if (mode === 'resize') {
        const dw = x - startX;
        const dh = y - startY;
        const nw = Math.max(20, origW + dw);
        const nh = Math.max(20, origH + dh);

        // Scale font size proportionally to height change (simple heuristic)
        const scale = nh / Math.max(1, origH);
        const nfs = Math.max(6, Math.round(origFS * scale));

        return { ...prev, [selectedTitle]: { ...b, width: Math.round(nw), height: Math.round(nh), font_size: nfs, max_width: Math.round(nw) } };
      }

      return prev;
    });
  };

  const onMouseUp = () => {
    dragState.current = { mode: null };
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
  };

  const onStageMouseDown = () => {
    setSelectedTitle(null);
    setMenu({ visible: false, x: 0, y: 0 });
  };

  const onBlockContextMenu = (e, title) => {
    e.preventDefault();
    setSelectedTitle(title);
    const rect = stageRef.current.getBoundingClientRect();
    setMenu({ visible: true, x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const applyMenuChange = (field, value) => {
    if (!selectedTitle) return;
    setBlocks((prev) => ({ ...prev, [selectedTitle]: { ...prev[selectedTitle], [field]: value } }));
  };

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

      // compatible with either immediate image_url or job style
      if (resp.data?.image_url) {
        setOutputUrl(resp.data.image_url);
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
      }
    } catch (e) {
      console.error(e);
      setError('Failed to start image generation.');
    } finally {
      setIsGenerating(false);
    }
  };

  if (!template) return <div style={{ padding: '2rem' }}>Loading…</div>;

  return (
    <div style={{ padding: '2rem', display: 'grid', gridTemplateColumns: '380px 1fr', gap: '1.5rem' }}>
      {/* Controls */}
      <div>
        <h2 style={{ marginTop: 0 }}>Customize: {template.name}</h2>

        {Object.values(blocks).map((b) => (
          <div key={b.title} style={{ borderBottom: '1px solid #eee', paddingBottom: '0.75rem', marginBottom: '0.75rem' }}>
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
          <div
            ref={stageRef}
            onMouseDown={onStageMouseDown}
            style={{
              position: 'relative',
              width: 715,
              height: 1144,
              border: '1px solid #000',
              backgroundImage: `url(${API_BASE}${template.image_path})`,
              backgroundSize: 'contain',
              backgroundRepeat: 'no-repeat',
              backgroundPosition: 'center',
              userSelect: 'none',
              overflow: 'hidden',
            }}
          >
            {Object.values(blocks).map((b) => {
              const selected = selectedTitle === b.title;
              return (
                <div
                  key={b.title}
                  onMouseDown={(e) => onBlockMouseDown(e, b.title)}
                  onContextMenu={(e) => onBlockContextMenu(e, b.title)}
                  style={{
                    position: 'absolute',
                    left: b.x,
                    top: b.y,
                    width: b.width,
                    height: b.height,
                    cursor: 'move',
                    outline: selected ? '2px dashed #3b82f6' : 'none',
                    padding: 2,
                  }}
                >
                  <div
                    style={{
                      fontSize: b.font_size,
                      color: b.color,
                      fontFamily: b.font_path ? 'inherit' : 'sans-serif',
                      width: '100%',
                      height: '100%',
                      overflow: 'hidden',
                      lineHeight: 1.25,
                      fontWeight: b.bold ? 700 : 400,
                      fontStyle: b.italic ? 'italic' : 'normal',
                      pointerEvents: 'none',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {b.user_text || b.title}
                  </div>

                  {/* Corner resize handle (bottom-right) */}
                  <div
                    onMouseDown={(e) => onHandleMouseDown(e, b.title)}
                    style={{
                      position: 'absolute',
                      right: -6,
                      bottom: -6,
                      width: 12,
                      height: 12,
                      background: '#3b82f6',
                      borderRadius: 2,
                      cursor: 'nwse-resize',
                    }}
                  />
                </div>
              );
            })}

            {/* Context menu */}
            {menu.visible && selectedTitle && (
              <div
                ref={contextMenuRef}
                style={{
                  position: 'absolute',
                  left: menu.x,
                  top: menu.y,
                  background: '#111',
                  color: '#fff',
                  padding: 10,
                  borderRadius: 6,
                  minWidth: 220,
                  zIndex: 10,
                }}
                onMouseDown={(e) => e.stopPropagation()}
              >
                <div style={{ marginBottom: 8, fontWeight: 600 }}>{selectedTitle}</div>
                <div style={{ display: 'grid', gap: 8 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 70 }}>Color</span>
                    <input
                      type="color"
                      value={blocks[selectedTitle].color}
                      onChange={(e) => applyMenuChange('color', e.target.value)}
                    />
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 70 }}>Font</span>
                    <select
                      value={blocks[selectedTitle].font_path || ''}
                      onChange={(e) => applyMenuChange('font_path', e.target.value || null)}
                    >
                      {defaultFonts.map((f) => (
                        <option key={f.label} value={f.value}>{f.label}</option>
                      ))}
                    </select>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 70 }}>Size</span>
                    <input
                      type="number"
                      min={6}
                      value={blocks[selectedTitle].font_size}
                      onChange={(e) => applyMenuChange('font_size', parseInt(e.target.value) || blocks[selectedTitle].font_size)}
                      style={{ width: 90 }}
                    />
                  </label>
                  <div style={{ display: 'flex', gap: 12 }}>
                    <label>
                      <input
                        type="checkbox"
                        checked={!!blocks[selectedTitle].bold}
                        onChange={(e) => applyMenuChange('bold', e.target.checked)}
                      /> Bold
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={!!blocks[selectedTitle].italic}
                        onChange={(e) => applyMenuChange('italic', e.target.checked)}
                      /> Italic
                    </label>
                  </div>
                </div>
              </div>
            )}
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
