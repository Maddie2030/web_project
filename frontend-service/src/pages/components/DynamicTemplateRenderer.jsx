// src/components/DynamicTemplateRenderer.jsx
import React, { useEffect, useRef } from 'react';
import * as fabric from 'fabric';

const ORIGINAL_W = 715;
const ORIGINAL_H = 1144;
const PREVIEW_W = ORIGINAL_W / 1.8;
const PREVIEW_H = ORIGINAL_H / 1.8;
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8003';

const DynamicTemplateRenderer = ({ template, resumeData }) => {
    const canvasRef = useRef(null);
    const fabricCanvasRef = useRef(null);

    useEffect(() => {
        if (!canvasRef.current || !template) return;

        if (!fabricCanvasRef.current) {
            fabricCanvasRef.current = new fabric.StaticCanvas(canvasRef.current, {
                width: PREVIEW_W,
                height: PREVIEW_H,
                backgroundColor: null,
            });
        }

        const canvas = fabricCanvasRef.current;
        canvas.clear();

        const renderResumeData = () => {
            if (!Array.isArray(template.text_blocks)) return;

            const scaleX = PREVIEW_W / ORIGINAL_W;
            const scaleY = PREVIEW_H / ORIGINAL_H;

            template.text_blocks.forEach((block) => {
                let content = '';
                const fieldMap = {
                    'FULL NAME': 'fullName',
                    'CONTACT INFO': 'contact',
                    'KEY SKILLS INFO': 'keySkills',
                    'EDUCATION INFO': 'education',
                    'PROFESSIONAL SUMMARY INFO': 'professionalSummary',
                    'WORK HISTORY INFO': 'workHistory',
                    'CERTIFICATIONS INFO': 'certifications',
                    // Add more mappings as needed
                };
                const resumeField = fieldMap[block.type];

                if (resumeField) {
                    const data = resumeData[resumeField];
                    if (data) {
                        if (typeof data === 'string') {
                            content = data;
                        } else if (Array.isArray(data)) {
                            content = data.join('\n');
                        } else if (typeof data === 'object') {
                            if (resumeField === 'contact') {
                                content = `Address :\n${data.address}\nPhone :\n${data.phone}\nE-mail :\n${data.email}`;
                            } else if (resumeField === 'education') {
                                content = `${data.year} - ${data.degree}\n${data.institution}`;
                            }
                        }
                    }
                }

                // Handle dynamic custom sections
                const isCustomSection = block.type.startsWith('CUSTOM_SECTION_');
                if (isCustomSection) {
                    const sectionId = block.type.split('_').pop();
                    const customSection = resumeData.customSections.find(s => s.id.toString() === sectionId);
                    if (customSection) {
                        content = `${customSection.title}\n${customSection.content}`;
                    }
                }
                
                // If content is empty, don't render the text block
                if (!content) return;

                const tb = new fabric.Textbox(content, {
                    left: block.x * scaleX,
                    top: block.y * scaleY,
                    width: block.width * scaleX,
                    fontSize: Math.max(block.font_size * scaleX, 8),
                    fill: block.color || "#000",
                    fontWeight: block.bold ? "bold" : "normal",
                    fontStyle: block.italic ? "italic" : "normal",
                    textAlign: block.text_align || "left",
                    selectable: false,
                    editable: false,
                });
                canvas.add(tb);
            });
            canvas.renderAll();
        };

        if (template?.image_path) {
            fabric.FabricImage.fromURL(`${API_BASE}${template.image_path}`, { crossOrigin: "anonymous" }).then(img => {
                if (!img) return;

                const scaleX = PREVIEW_W / img.width;
                const scaleY = PREVIEW_H / img.height;
                const scale = Math.min(scaleX, scaleY);

                img.scale(scale);
                img.set({
                    left: (canvas.getWidth() - img.width * scale) / 2,
                    top: (canvas.getHeight() - img.height * scale) / 2,
                    originX: 'left',
                    originY: 'top',
                    selectable: false,
                    evented: false,
                });

                canvas.backgroundImage = img;
                canvas.renderAll();
                renderResumeData();
            });
        }
    }, [template, resumeData]);

    return <canvas ref={canvasRef} className="w-full h-full object-cover" />;
};

export default DynamicTemplateRenderer;