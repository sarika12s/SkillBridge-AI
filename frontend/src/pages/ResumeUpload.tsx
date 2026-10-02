import React, { useState, useEffect } from 'react';
import { ResumeUploader } from '../components/resume/ResumeUploader';
import { UploadProgress } from '../components/resume/UploadProgress';
import { ResumePreview } from '../components/resume/ResumePreview';
import { listResumes, getResumeById, deleteResume } from '../services/resumeService';
import type { StructuredResume, ResumeSummary } from '../types/resume';
import { FileText, Trash2, Eye, Clock } from 'lucide-react';

export const ResumeUploadPage: React.FC = () => {
  const [activeResume, setActiveResume] = useState<StructuredResume | null>(null);
  const [uploadStage, setUploadStage] = useState<
    'uploading' | 'validating' | 'extracting' | 'segmenting' | 'completed' | null
  >(null);
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [recentResumes, setRecentResumes] = useState<ResumeSummary[]>([]);
  const [loadingRecent, setLoadingRecent] = useState<boolean>(false);

  const fetchRecent = async () => {
    setLoadingRecent(true);
    try {
      const data = await listResumes();
      setRecentResumes(data);
    } catch {
      // User might not be logged in yet
      setRecentResumes([]);
    } finally {
      setLoadingRecent(false);
    }
  };

  useEffect(() => {
    fetchRecent();
  }, []);

  const handleUploadStart = () => {
    setUploadStage('uploading');
    setProgressPercent(15);
  };

  const handleProgress = (percent: number) => {
    setProgressPercent(percent);
    if (percent >= 100) {
      setUploadStage('extracting');
    }
  };

  const handleUploadSuccess = (resume: StructuredResume) => {
    setUploadStage('completed');
    setTimeout(() => {
      setActiveResume(resume);
      setUploadStage(null);
      fetchRecent();
    }, 600);
  };

  const handleSelectRecent = async (id: string) => {
    try {
      const full = await getResumeById(id);
      setActiveResume(full);
    } catch (err: any) {
      alert('Failed to load resume: ' + (err?.message || 'Unknown error'));
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this resume?')) return;
    try {
      await deleteResume(id);
      if (activeResume?.id === id) {
        setActiveResume(null);
      }
      fetchRecent();
    } catch (err: any) {
      alert('Failed to delete resume: ' + (err?.message || 'Unknown error'));
    }
  };

  return (
    <div className="space-y-8">
      {/* If actively viewing a parsed resume */}
      {activeResume ? (
        <ResumePreview
          resume={activeResume}
          onReset={() => setActiveResume(null)}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Upload Column */}
          <div className="lg:col-span-2 space-y-6">
            {uploadStage ? (
              <UploadProgress
                stage={uploadStage}
                progressPercent={progressPercent}
              />
            ) : (
              <ResumeUploader
                onUploadStart={handleUploadStart}
                onProgress={handleProgress}
                onUploadSuccess={handleUploadSuccess}
              />
            )}
          </div>

          {/* Recently Uploaded Sidebar */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4 h-fit">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                  Uploaded Resumes
                </h4>
              </div>
              <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-semibold">
                {recentResumes.length}
              </span>
            </div>

            {loadingRecent ? (
              <p className="text-xs text-slate-400 py-4 text-center">Loading resumes...</p>
            ) : recentResumes.length === 0 ? (
              <div className="text-center py-6 space-y-1">
                <FileText className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-xs text-slate-500 font-medium">No resumes uploaded yet</p>
                <p className="text-[11px] text-slate-400">
                  Upload a PDF or DOCX file to see parsed results here.
                </p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[450px] overflow-y-auto pr-1">
                {recentResumes.map((r) => (
                  <div
                    key={r.id}
                    onClick={() => handleSelectRecent(r.id)}
                    className="p-3 rounded-xl border border-slate-200 hover:border-blue-400 hover:bg-blue-50/20 cursor-pointer transition flex items-center justify-between group"
                  >
                    <div className="truncate space-y-0.5">
                      <p className="text-xs font-bold text-slate-800 truncate group-hover:text-blue-600">
                        {r.title}
                      </p>
                      <div className="flex items-center space-x-2 text-[11px] text-slate-400 font-mono">
                        <span className="uppercase font-semibold">{r.file_type}</span>
                        <span>&bull;</span>
                        <span>{r.sections_count} sections</span>
                        <span>&bull;</span>
                        <span className={r.extraction_method === 'OCR' ? 'text-purple-600 font-semibold' : ''}>
                          {r.extraction_method}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-1 shrink-0 ml-2">
                      <button
                        title="View details"
                        className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={(e) => handleDelete(r.id, e)}
                        title="Delete resume"
                        className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
