//frontend-service/src/pages/DashboardPage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { Plus, FileText, Download, Edit, Star } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

const DashboardPage = () => {
  const token = useAuthStore((state) => state.token);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Create Professional Resumes in Minutes
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          Build stunning resumes with our AI-powered templates and land your dream job.
        </p>
        <Link
          to="/templates"
          className="inline-flex items-center space-x-2 bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-all duration-200 transform hover:scale-105"
        >
          <Plus className="h-5 w-5" />
          <span>Create New Resume</span>
        </Link>
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex items-center">
            <FileText className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">50+</p>
              <p className="text-sm text-gray-600">Professional Templates</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex items-center">
            <Download className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">1M+</p>
              <p className="text-sm text-gray-600">Downloads</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex items-center">
            <Star className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">4.9/5</p>
              <p className="text-sm text-gray-600">User Rating</p>
            </div>
          </div>
        </div>
      </div>

      {token && (
        <>
          {/* Section for displaying your original templates */}
          <div className="mb-12">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Your Generated Images</h2>
              <Link
                to="/templates"
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                View all templates
              </Link>
            </div>
            {/* The actual list of generated images can be implemented here */}
          </div>
        </>
      )}

      {/* Features Section */}
      <div className="bg-white rounded-lg p-8 shadow-sm border border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">Why Choose Our Service?</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="bg-blue-100 rounded-full p-3 w-12 h-12 mx-auto mb-4 flex items-center justify-center">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Professional Templates</h3>
            <p className="text-gray-600">Choose from 50+ professionally designed templates crafted by industry experts.</p>
          </div>
          <div className="text-center">
            <div className="bg-green-100 rounded-full p-3 w-12 h-12 mx-auto mb-4 flex items-center justify-center">
              <Edit className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Easy Customization</h3>
            <p className="text-gray-600">Our powerful editors make customization effortless, whether for resumes or other templates.</p>
          </div>
          <div className="text-center">
            <div className="bg-purple-100 rounded-full p-3 w-12 h-12 mx-auto mb-4 flex items-center justify-center">
              <Download className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Instant Download</h3>
            <p className="text-gray-600">Download your creations as PDFs or high-quality images instantly.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;