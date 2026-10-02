import React, { useState } from 'react';
import { Navbar } from './components/layout/Navbar';
import { AuthBanner } from './components/auth/AuthBanner';
import { ResumeUploadPage } from './pages/ResumeUpload';
import { JobUploadPage } from './pages/JobUpload';
import { MatchingDashboard } from './pages/MatchingDashboard';
import { CareerCompatibility } from './pages/CareerCompatibility';
import { LearningPathView } from './pages/LearningPathView';
import { CareerDashboard } from './pages/CareerDashboard';
import { ResumeVersions } from './pages/ResumeVersions';
import {
  FileUp,
  Briefcase,
  GitCompare,
  Compass,
  GraduationCap,
  Info,
  ExternalLink,
  ShieldCheck,
  LayoutDashboard,
  Layers,
} from 'lucide-react';

export const App: React.FC = () => {
  const [activeView, setActiveView] = useState<
    'dashboard' | 'versions' | 'resumes' | 'jobs' | 'matching' | 'careers' | 'learning' | 'about'
  >('dashboard');

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Academic Project Title Header */}
        <section className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-2">
              <span className="inline-flex items-center text-xs font-semibold uppercase tracking-wider text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-full">
                Final-Year Capstone Engineering Project
              </span>
              <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 leading-tight">
                Semantic Resume - Job Matching and Skill Gap Analysis with Personalized Learning Path Recommendation
              </h2>
              <p className="text-slate-600 text-xs sm:text-sm max-w-3xl leading-relaxed">
                Phase 7 Intelligence: Interactive Career Intelligence Dashboard, Resume Version Tracking, Skill Trajectory Analytics,
                and Progress Roadmaps.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-2 shrink-0">
              <a
                href="http://localhost:8000/api/v1/docs"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center space-x-2 text-xs font-medium text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 border border-blue-200 px-3.5 py-2 rounded-lg transition"
              >
                <span>Interactive OpenAPI Docs</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          {/* Navigation Bar for Views */}
          <div className="flex flex-wrap border-t border-slate-100 mt-6 pt-4 gap-2 text-xs font-semibold">
            <button
              onClick={() => setActiveView('dashboard')}
              className={`px-3.5 py-2 rounded-lg transition flex items-center space-x-2 ${
                activeView === 'dashboard'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Career Dashboard</span>
            </button>

            <button
              onClick={() => setActiveView('versions')}
              className={`px-3.5 py-2 rounded-lg transition flex items-center space-x-2 ${
                activeView === 'versions'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Resume Versions</span>
            </button>

            <button
              onClick={() => setActiveView('resumes')}
              className={`px-3.5 py-2 rounded-lg transition flex items-center space-x-2 ${
                activeView === 'resumes'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <FileUp className="w-4 h-4" />
              <span>Resumes & Skills</span>
            </button>

            <button
              onClick={() => setActiveView('jobs')}
              className={`px-3.5 py-2 rounded-lg transition flex items-center space-x-2 ${
                activeView === 'jobs'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Briefcase className="w-4 h-4" />
              <span>Job Requirements</span>
            </button>

            <button
              onClick={() => setActiveView('matching')}
              className={`px-3.5 py-2 rounded-lg transition flex items-center space-x-2 ${
                activeView === 'matching'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <GitCompare className="w-4 h-4" />
              <span>Matching & Gaps</span>
            </button>

            <button
              onClick={() => setActiveView('careers')}
              className={`px-3.5 py-2 rounded-lg transition flex items-center space-x-2 ${
                activeView === 'careers'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Compass className="w-4 h-4" />
              <span>Career Roles (Phase 6)</span>
            </button>

            <button
              onClick={() => setActiveView('learning')}
              className={`px-3.5 py-2 rounded-lg transition flex items-center space-x-2 ${
                activeView === 'learning'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <GraduationCap className="w-4 h-4" />
              <span>Learning Paths & DAG (Phase 6)</span>
            </button>

            <button
              onClick={() => setActiveView('about')}
              className={`px-3.5 py-2 rounded-lg transition flex items-center space-x-2 ${
                activeView === 'about'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Info className="w-4 h-4" />
              <span>Pipeline & Specs</span>
            </button>
          </div>
        </section>

        {/* Authentication Session Banner */}
        <AuthBanner />

        {/* View Content */}
        {activeView === 'dashboard' && <CareerDashboard />}
        {activeView === 'versions' && <ResumeVersions />}
        {activeView === 'resumes' && <ResumeUploadPage />}
        {activeView === 'jobs' && <JobUploadPage />}
        {activeView === 'matching' && <MatchingDashboard />}
        {activeView === 'careers' && <CareerCompatibility />}
        {activeView === 'learning' && <LearningPathView />}
        {activeView === 'about' && (
          <section className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
            <div className="flex items-center space-x-2 text-sm font-bold text-slate-800 uppercase tracking-wider">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              <h3>Phase 2 Technical Ingestion Pipeline</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <h4 className="font-bold text-slate-900 text-sm">1. Document Parsers</h4>
                <p className="text-slate-600 leading-relaxed">
                  PyMuPDF (<code className="font-mono text-blue-600">fitz</code>) performs page-by-page PDF extraction with line boundary normalization.
                  <code className="font-mono text-blue-600">python-docx</code> extracts structured paragraphs, headings, and tabular cells.
                </p>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <h4 className="font-bold text-slate-900 text-sm">2. Text Quality & OCR Fallback</h4>
                <p className="text-slate-600 leading-relaxed">
                  Evaluates character counts, meaningful word density, and alphabetic ratios.
                  Scanned documents trigger Tesseract OCR via PyMuPDF 300 DPI pixmap rendering.
                </p>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <h4 className="font-bold text-slate-900 text-sm">3. Section & Entity Extraction</h4>
                <p className="text-slate-600 leading-relaxed">
                  Normalizes headings (Summary, Education, Experience, Projects, Skills, Certifications) and extracts contact details (email, phone, LinkedIn, GitHub) deterministically.
                </p>
              </div>
            </div>
          </section>
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        SkillBridge AI &bull; Official Final-Year Capstone Project &bull; Academic Decision-Support System
      </footer>
    </div>
  );
};

export default App;
