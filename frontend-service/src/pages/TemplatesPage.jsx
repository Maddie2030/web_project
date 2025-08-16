// frontend-service/src/pages/TemplatesPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, Filter, Star, Eye } from 'lucide-react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import * as fabric from 'fabric';
import { Canvas, FabricImage, Textbox } from 'fabric';

const CANVAS_W = 474;
const CANVAS_H = 796;

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8003';

// Component to render each template preview
// 🔑 Added `showTextBlocks` prop (defaults to true)
const TemplateThumbnail = ({ template, showTextBlocks = true }) => {
  const canvasRef = useRef(null);
  const fabricCanvasRef = useRef(null);

    useEffect(() => {
    if (!canvasRef.current) return;

    if (!fabricCanvasRef.current) {
      fabricCanvasRef.current = new fabric.StaticCanvas(canvasRef.current, {
        width: CANVAS_W / 4,
        height: CANVAS_H / 4,
        backgroundColor: null,
      });
    }

    const canvas = fabricCanvasRef.current;
    canvas.clear();

    if (template?.image_path) {
      FabricImage.fromURL(`${API_BASE}${template.image_path}`, { crossOrigin: "anonymous" }).then(img => {
        if (!img) return;

        const scaleX = canvas.getWidth() / img.width;
        const scaleY = canvas.getHeight() / img.height;
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

        if (showTextBlocks && Array.isArray(template.text_blocks)) {
          template.text_blocks.forEach((block) => {
            const tb = new fabric.Textbox(block.default_text || block.content || "", {
              left: block.x * scale,
              top: block.y * scale,
              width: block.width * scale,
              fontSize: block.font_size * scale,
              fill: block.color || "#000",
              fontWeight: block.font_weight || "normal",
              fontStyle: block.font_style || "normal",
              textAlign: block.text_align || "left",
              selectable: false,
              editable: false,
            });
            canvas.add(tb);
          });
        }
        canvas.renderAll();
      });
    }
  }, [template, showTextBlocks]);


  return <canvas ref={canvasRef} />;
};

const TemplatesPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const token = useAuthStore((state) => state.token);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE}/api/v1/templates/templates`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setTemplates(response.data);
      } catch (error) {
        console.error('Failed to fetch templates:', error);
      } finally {
        setLoading(false);
      }
    };
    if (token) fetchTemplates();
  }, [token]);

  const categories = ['All', 'Modern', 'Professional', 'Creative', 'Minimal', 'Executive'];

  const filteredTemplates = templates.filter((template) => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory =
      selectedCategory === 'All' ||
      (template.category && template.category.toLowerCase() === selectedCategory.toLowerCase());
    return matchesSearch && matchesCategory;
  });

  if (loading) {
    return <div className="text-center py-12">Loading templates...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Choose Your Perfect Template</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Select from our collection of professionally designed templates, each optimized for different industries and career levels.
        </p>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="h-5 w-5 text-gray-400" />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {categories.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Templates Grid */}
      <div className="overflow-x-auto py-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
          {filteredTemplates.map((template) => (
            <div
              key={template._id || template.id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-lg transition-all duration-300 transform hover:scale-105"
            >
              {/* Template Preview */}
              <div className="relative group aspect-[1/0.8] overflow-hidden">
                {/* 🔑 Thumbnail with background + text blocks */}
                <TemplateThumbnail template={template} showTextBlocks={true} />
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-300 flex items-center justify-center space-x-4">
                  <Link
                    to={`/text-entry/${template._id || template.id}`}
                    className="opacity-0 group-hover:opacity-100 bg-white text-gray-900 px-4 py-2 rounded-lg font-medium flex items-center space-x-2 transform translate-y-2 group-hover:translate-y-0 transition-all duration-300"
                  >
                    <Eye className="h-4 w-4" />
                    <span>Preview</span>
                  </Link>
                </div>
              </div>

              {/* Template Info */}
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {template.name}
                  </h3>
                  <div className="flex items-center space-x-1">
                    <Star className="h-4 w-4 text-yellow-400 fill-current" />
                    <span className="text-sm text-gray-600">4.9</span>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                  <span className="bg-gray-100 px-2 py-1 rounded">
                    {template.category || 'Professional'}
                  </span>
                  <span>12K downloads</span>
                </div>
                <button
                  onClick={() => navigate(`/text-entry/${template._id || template.id}`)}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium"
                >
                  Use This Template
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No templates found matching your criteria.</p>
        </div>
      )}
    </div>
  );
};

export default TemplatesPage;
