import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { learningService } from '../services/learningService';
import type { LearningPath } from '../types/learning';
import { LearningStageCard } from '../components/learning/LearningStageCard';
import { DependencyGraphVisualizer } from '../components/learning/DependencyGraphVisualizer';
import {
  BookOpen,
  GitBranch,
  Clock,
  ListOrdered,
  AlertCircle,
  RotateCw,
  ArrowLeft,
} from 'lucide-react';

export const LearningPathView: React.FC = () => {
  const { pathId } = useParams<{ pathId: string }>();
  const navigate = useNavigate();

  const [path, setPath] = useState<LearningPath | null>(null);
  const [allPaths, setAllPaths] = useState<any[]>([]);
  const [selectedPathId, setSelectedPathId] = useState<string>(pathId || '');
  const [activeTab, setActiveTab] = useState<'curriculum' | 'graph'>('curriculum');

  const [loading, setLoading] = useState<boolean>(true);
  const [updatingItemId, setUpdatingItemId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUserPaths();
  }, []);

  useEffect(() => {
    if (selectedPathId) {
      loadPathDetails(selectedPathId);
    }
  }, [selectedPathId]);

  const loadUserPaths = async () => {
    try {
      const paths = await learningService.listLearningPaths();
      setAllPaths(paths);
      if (!pathId && paths.length > 0) {
        setSelectedPathId(paths[0].id);
      }
    } catch (err: any) {
      // Non-blocking
    }
  };

  const loadPathDetails = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await learningService.getLearningPath(id);
      setPath(data);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || 'Failed to load personalized learning path.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateItemStatus = async (
    itemId: string,
    newStatus: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED'
  ) => {
    setUpdatingItemId(itemId);
    try {
      const res = await learningService.updateItemProgress(itemId, newStatus);
      // Update local state smoothly
      if (path) {
        const updatedStages = path.stages.map((stg) => ({
          ...stg,
          items: stg.items.map((it) =>
            it.id === itemId
              ? { ...it, status: newStatus, completed_at: res.completed_at }
              : it
          ),
        }));

        const updatedGraph = path.graph
          ? {
              ...path.graph,
              nodes: path.graph.nodes.map((node) => {
                const matchedItem = path.stages
                  .flatMap((s) => s.items)
                  .find((i) => i.id === itemId);
                if (matchedItem && matchedItem.skill_name === node.id) {
                  return { ...node, status: newStatus };
                }
                return node;
              }),
            }
          : undefined;

        setPath({
          ...path,
          overall_progress_percentage: res.overall_progress_percentage,
          status: res.path_status,
          stages: updatedStages,
          graph: updatedGraph,
        });
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update item progress.');
    } finally {
      setUpdatingItemId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Navigation & Path Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <button
          onClick={() => navigate('/careers')}
          className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Career Compatibility</span>
        </button>

        {allPaths.length > 1 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Your Roadmaps:</span>
            <select
              value={selectedPathId}
              onChange={(e) => setSelectedPathId(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500"
            >
              {allPaths.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title} ({p.overall_progress_percentage}%)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loading ? (
        <div className="p-16 text-center bg-slate-900 border border-slate-800 rounded-2xl">
          <RotateCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-400">Loading personalized learning curriculum & DAG...</p>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      ) : path ? (
        <div>
          {/* Path Header Banner */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
              <div className="max-w-3xl">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    {path.target_type === 'CAREER' ? 'Career Role Pathway' : 'Job Role Target'}
                  </span>
                  {path.target_title && (
                    <span className="text-xs text-slate-400 font-medium">
                      Target: {path.target_title}
                    </span>
                  )}
                </div>
                <h1 className="text-2xl font-black text-slate-100 tracking-tight">
                  {path.title}
                </h1>
                <p className="text-slate-400 text-sm mt-1 leading-relaxed">
                  {path.description}
                </p>
              </div>

              {/* Progress Summary Card */}
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 min-w-[260px] space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400 font-medium">Overall Completion</span>
                  <span className="font-bold text-slate-100">{path.overall_progress_percentage}%</span>
                </div>

                <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full transition-all duration-500"
                    style={{ width: `${path.overall_progress_percentage}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400 pt-1 border-t border-slate-800/80">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-indigo-400" />
                    {path.total_estimated_hours_min} - {path.total_estimated_hours_max}h total
                  </span>
                  <span
                    className={`font-semibold ${
                      path.status === 'COMPLETED' ? 'text-emerald-400' : 'text-blue-400'
                    }`}
                  >
                    {path.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            </div>

            {/* View Switcher Tabs */}
            <div className="flex items-center gap-2 mt-6 pt-4 border-t border-slate-800">
              <button
                onClick={() => setActiveTab('curriculum')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
                  activeTab === 'curriculum'
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                    : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
                }`}
              >
                <ListOrdered className="w-4 h-4" />
                <span>Staged Curriculum</span>
              </button>

              <button
                onClick={() => setActiveTab('graph')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
                  activeTab === 'graph'
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                    : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
                }`}
              >
                <GitBranch className="w-4 h-4" />
                <span>Interactive Skill Dependency Graph (DAG)</span>
              </button>
            </div>
          </div>

          {/* Tab Content */}
          {activeTab === 'curriculum' ? (
            <div>
              {path.stages.map((stg) => (
                <LearningStageCard
                  key={stg.stage_number}
                  stage={stg}
                  onUpdateItemStatus={handleUpdateItemStatus}
                  updatingItemId={updatingItemId}
                />
              ))}
            </div>
          ) : (
            <DependencyGraphVisualizer graph={path.graph} />
          )}
        </div>
      ) : (
        <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-2xl text-slate-400">
          <BookOpen className="w-8 h-8 text-slate-500 mx-auto mb-2" />
          <p className="text-sm">No learning paths found. Go to Career Compatibility to generate one!</p>
        </div>
      )}
    </div>
  );
};
