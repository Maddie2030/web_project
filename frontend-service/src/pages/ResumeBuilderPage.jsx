// frontend-service/src/pages/ResumeBuilderPage.jsx
import React, { useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Save, Download, Eye, EyeOff, Plus, Trash2, User, Briefcase, GraduationCap, Phone, Mail, MapPin } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { useResumeStore } from '../store/resumeStore';

const ResumeBuilderPage = () => {
    const { templateId } = useParams();
    const [showPreview, setShowPreview] = useState(true);
    const resumeRef = useRef(null);
    const navigate = useNavigate();

    // Use the state and actions from the global store
    const {
        resumeData,
        setFullName,
        setContactInfo,
        setSummary,
        setSkills,
        addSkill,
        removeSkill,
        setWorkHistory,
        addWorkHistoryEntry,
        removeWorkHistoryEntry,
        setCertifications,
        addCertification,
        removeCertification,
        addCustomSection,
        updateCustomSection,
        removeCustomSection
    } = useResumeStore();

    const downloadPDF = () => {
        alert('PDF download feature would be implemented here.');
    };

    const saveAndRedirectToTemplates = () => {
        navigate('/templates');
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Toolbar - No changes */}
            <div className="bg-white border-b border-gray-200 px-4 py-3">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <h1 className="text-xl font-semibold text-gray-900">Resume Builder</h1>
                        <button
                            onClick={() => setShowPreview(!showPreview)}
                            className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                        >
                            {showPreview ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            <span>{showPreview ? 'Hide Preview' : 'Show Preview'}</span>
                        </button>
                    </div>
                    <div className="flex items-center space-x-3">
                        <button
                            onClick={saveAndRedirectToTemplates}
                            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                            <Save className="h-4 w-4" />
                            <span>Save & View Templates</span>
                        </button>
                        <button
                            onClick={downloadPDF}
                            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                        >
                            <Download className="h-4 w-4" />
                            <span>Download PDF</span>
                        </button>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto flex">
                {/* Editor Panel */}
                <div className={`p-6 overflow-y-auto max-h-screen ${showPreview ? 'w-1/2' : 'w-full'}`}>
                    <div className="space-y-8">
                        {/* Personal Information */}
                        <div className="bg-white rounded-lg p-6 shadow-sm">
                            <div className="flex items-center space-x-2 mb-4">
                                <User className="h-5 w-5 text-blue-600" />
                                <h2 className="text-lg font-semibold">Personal Information</h2>
                            </div>
                            <input
                                type="text"
                                placeholder="Full Name"
                                value={resumeData.fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 mb-4"
                            />
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <input
                                    type="text"
                                    placeholder="Address"
                                    value={resumeData.contact.address}
                                    onChange={(e) => setContactInfo('address', e.target.value)}
                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                />
                                <input
                                    type="email"
                                    placeholder="E-mail"
                                    value={resumeData.contact.email}
                                    onChange={(e) => setContactInfo('email', e.target.value)}
                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                />
                                <input
                                    type="tel"
                                    placeholder="Phone"
                                    value={resumeData.contact.phone}
                                    onChange={(e) => setContactInfo('phone', e.target.value)}
                                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        </div>

                        {/* Professional Summary */}
                        <div className="bg-white rounded-lg p-6 shadow-sm">
                            <h2 className="text-lg font-semibold mb-4">Professional Summary</h2>
                            <textarea
                                rows={4}
                                placeholder="Write a brief summary..."
                                value={resumeData.professionalSummary}
                                onChange={(e) => setSummary(e.target.value)}
                                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Work History */}
                        <div className="bg-white rounded-lg p-6 shadow-sm">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center space-x-2">
                                    <Briefcase className="h-5 w-5 text-blue-600" />
                                    <h2 className="text-lg font-semibold">Work History</h2>
                                </div>
                                <button
                                    onClick={addWorkHistoryEntry}
                                    className="flex items-center space-x-1 text-blue-600 hover:text-blue-700"
                                >
                                    <Plus className="h-4 w-4" />
                                    <span>Add Entry</span>
                                </button>
                            </div>
                            <div className="space-y-4">
                                {resumeData.workHistory.map((entry, index) => (
                                    <div key={index} className="flex space-x-2 items-center">
                                        <textarea
                                            rows={2}
                                            placeholder="Describe your role..."
                                            value={entry}
                                            onChange={(e) => {
                                                const updatedHistory = [...resumeData.workHistory];
                                                updatedHistory[index] = e.target.value;
                                                setWorkHistory(updatedHistory);
                                            }}
                                            className="flex-1 p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                        />
                                        <button
                                            onClick={() => removeWorkHistoryEntry(index)}
                                            className="text-red-500 hover:text-red-700"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Key Skills */}
                        <div className="bg-white rounded-lg p-6 shadow-sm">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold">Key Skills</h2>
                                <button
                                    onClick={addSkill}
                                    className="flex items-center space-x-1 text-blue-600 hover:text-blue-700"
                                >
                                    <Plus className="h-4 w-4" />
                                    <span>Add Skill</span>
                                </button>
                            </div>
                            <div className="space-y-2">
                                {resumeData.keySkills.map((skill, index) => (
                                    <div key={index} className="flex space-x-2 items-center">
                                        <input
                                            type="text"
                                            value={skill}
                                            onChange={(e) => {
                                                const updatedSkills = [...resumeData.keySkills];
                                                updatedSkills[index] = e.target.value;
                                                setSkills(updatedSkills);
                                            }}
                                            className="flex-1 p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                        />
                                        <button
                                            onClick={() => removeSkill(index)}
                                            className="text-red-500 hover:text-red-700"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Certifications - same logic as skills, but for certifications */}
                        <div className="bg-white rounded-lg p-6 shadow-sm">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold">Certifications</h2>
                                <button
                                    onClick={addCertification}
                                    className="flex items-center space-x-1 text-blue-600 hover:text-blue-700"
                                >
                                    <Plus className="h-4 w-4" />
                                    <span>Add Certification</span>
                                </button>
                            </div>
                            <div className="space-y-2">
                                {resumeData.certifications.map((cert, index) => (
                                    <div key={index} className="flex space-x-2 items-center">
                                        <input
                                            type="text"
                                            value={cert}
                                            onChange={(e) => {
                                                const updatedCerts = [...resumeData.certifications];
                                                updatedCerts[index] = e.target.value;
                                                setCertifications(updatedCerts);
                                            }}
                                            className="flex-1 p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                        />
                                        <button
                                            onClick={() => removeCertification(index)}
                                            className="text-red-500 hover:text-red-700"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                        
                        {/* New section for dynamic custom fields */}
                        <div className="bg-white rounded-lg p-6 shadow-sm">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold">Custom Sections</h2>
                                <button
                                    onClick={addCustomSection}
                                    className="flex items-center space-x-1 text-blue-600 hover:text-blue-700"
                                >
                                    <Plus className="h-4 w-4" />
                                    <span>Add Section</span>
                                </button>
                            </div>
                            <div className="space-y-4">
                                {resumeData.customSections.map((section) => (
                                    <div key={section.id} className="border border-gray-200 rounded-lg p-4">
                                        <div className="flex justify-between items-start mb-3">
                                            <input
                                                type="text"
                                                placeholder="Section Title"
                                                value={section.title}
                                                onChange={(e) => updateCustomSection(section.id, 'title', e.target.value)}
                                                className="w-full p-2 font-medium border-b border-gray-300 focus:outline-none"
                                            />
                                            <button
                                                onClick={() => removeCustomSection(section.id)}
                                                className="text-red-500 hover:text-red-700 ml-2"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </button>
                                        </div>
                                        <textarea
                                            rows={3}
                                            placeholder="Section Content"
                                            value={section.content}
                                            onChange={(e) => updateCustomSection(section.id, 'content', e.target.value)}
                                            className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>

                    </div>
                </div>

                {/* Preview Panel - now includes the custom fields */}
                {showPreview && (
                    <div className="w-1/2 p-6 bg-white border-l border-gray-200">
                        <div className="sticky top-6">
                            <div
                                ref={resumeRef}
                                className="bg-white shadow-lg rounded-lg p-8 max-w-2xl mx-auto"
                                style={{ minHeight: '800px' }}
                            >
                                {/* Header */}
                                <div className="text-center mb-8">
                                    <h1 className="text-3xl font-bold text-gray-900 mb-2">{resumeData.fullName}</h1>
                                    <div className="flex flex-wrap justify-center gap-4 text-sm text-gray-600">
                                        {resumeData.contact.email && (<div className="flex items-center space-x-1"><Mail className="h-4 w-4" /><span>{resumeData.contact.email}</span></div>)}
                                        {resumeData.contact.phone && (<div className="flex items-center space-x-1"><Phone className="h-4 w-4" /><span>{resumeData.contact.phone}</span></div>)}
                                        {resumeData.contact.address && (<div className="flex items-center space-x-1"><MapPin className="h-4 w-4" /><span>{resumeData.contact.address}</span></div>)}
                                    </div>
                                </div>
                                {/* ... (other sections like summary, work history, skills, etc.) ... */}

                                {/* Dynamic Sections - rendered from the store */}
                                {resumeData.customSections.map(section => (
                                    <div key={section.id} className="mb-8">
                                        <h2 className="text-lg font-semibold text-gray-900 border-b-2 border-blue-600 pb-1 mb-3">
                                            {section.title || 'Custom Section'}
                                        </h2>
                                        <p className="text-gray-700 leading-relaxed">{section.content}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ResumeBuilderPage;