import React, { useState, useEffect } from 'react';
import { 
  Briefcase, 
  Trash2, 
  Eye, 
  Sparkles, 
  Building2, 
  MapPin
} from 'lucide-react';
import { JobUploader } from '../components/jobs/JobUploader';
import { JobPreview } from '../components/jobs/JobPreview';
import { listJobs, getJobById, deleteJob } from '../services/jobService';
import type { StructuredJob, JobSummary } from '../types/job';

export const JobUploadPage: React.FC = () => {
  const [activeJob, setActiveJob] = useState<StructuredJob | null>(null);
  const [recentJobs, setRecentJobs] = useState<JobSummary[]>([]);
  const [loadingRecent, setLoadingRecent] = useState<boolean>(false);

  const fetchRecent = async () => {
    setLoadingRecent(true);
    try {
      const data = await listJobs();
      setRecentJobs(data);
    } catch {
      setRecentJobs([]);
    } finally {
      setLoadingRecent(false);
    }
  };

  useEffect(() => {
    fetchRecent();
  }, []);

  const handleSelectJob = async (id: string) => {
    try {
      const full = await getJobById(id);
      setActiveJob(full);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to load job profile.');
    }
  };

  const handleDeleteJob = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this job description?')) return;

    try {
      await deleteJob(id);
      if (activeJob?.id === id) {
        setActiveJob(null);
      }
      fetchRecent();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete job description.');
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Page Title */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-blue-500" />
            Phase 4 Intelligence
          </span>
          <span className="text-xs text-slate-400 font-mono">Pasted &bull; PDF &bull; DOCX</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Job Description Ingestion & Requirement Classification
        </h1>
        <p className="text-sm text-slate-600 max-w-3xl leading-relaxed">
          Ingest target job postings to automatically extract structured requirements, detect sections, classify canonical career roles, and normalize required vs. preferred skills against ESCO and O*NET taxonomies.
        </p>
      </div>

      {/* Main Content Area */}
      {activeJob ? (
        <JobPreview
          job={activeJob}
          onReset={() => setActiveJob(null)}
        />
      ) : (
        <JobUploader
          onSuccess={(job) => {
            setActiveJob(job);
            fetchRecent();
          }}
        />
      )}

      {/* Previously Analyzed Job Descriptions */}
      {!activeJob && (
        <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-blue-600" />
              <span>Previously Analyzed Jobs ({recentJobs.length})</span>
            </h3>
            <button
              onClick={fetchRecent}
              disabled={loadingRecent}
              className="text-xs font-medium text-slate-500 hover:text-blue-600 transition"
            >
              Refresh
            </button>
          </div>

          {loadingRecent ? (
            <div className="py-8 text-center text-xs text-slate-400">Loading recent jobs...</div>
          ) : recentJobs.length === 0 ? (
            <div className="p-8 text-center bg-slate-50 rounded-2xl border border-slate-100 text-xs text-slate-500">
              No job descriptions ingested yet. Paste a job post or upload a PDF/DOCX document above to begin.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recentJobs.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleSelectJob(item.id)}
                  className="p-5 rounded-2xl border border-slate-200 hover:border-blue-400 bg-white hover:bg-blue-50/20 transition cursor-pointer flex flex-col justify-between space-y-4 group shadow-2xs"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                        {item.ingestion_type}
                      </span>
                      <span className="text-xs font-semibold text-blue-600">
                        {item.normalized_role}
                      </span>
                    </div>

                    <h4 className="text-base font-bold text-slate-900 group-hover:text-blue-600 transition">
                      {item.title}
                    </h4>

                    {(item.company || item.location) && (
                      <div className="flex items-center gap-3 text-xs text-slate-500 pt-0.5">
                        {item.company && (
                          <span className="flex items-center gap-1">
                            <Building2 className="w-3.5 h-3.5 text-slate-400" />
                            {item.company}
                          </span>
                        )}
                        {item.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5 text-slate-400" />
                            {item.location}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 font-semibold text-[11px] border border-emerald-200">
                        {item.required_skills_count} Req Skills
                      </span>
                      <span className="px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 font-semibold text-[11px] border border-blue-200">
                        {item.preferred_skills_count} Pref
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectJob(item.id);
                        }}
                        className="p-1.5 text-slate-400 hover:text-blue-600 rounded-lg hover:bg-slate-100 transition"
                        title="View Profile"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => handleDeleteJob(item.id, e)}
                        className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition"
                        title="Delete Job"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
