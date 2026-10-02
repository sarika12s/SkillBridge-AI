import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import type { ScoreHistoryItem } from '../../types/dashboard';
import { TrendingUp, Info } from 'lucide-react';

interface ScoreTrendChartProps {
  scoreTrends: ScoreHistoryItem[];
}

export const ScoreTrendChart: React.FC<ScoreTrendChartProps> = ({ scoreTrends }) => {
  if (!scoreTrends || scoreTrends.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col items-center justify-center min-h-[300px] text-center">
        <div className="p-3 bg-slate-800/50 rounded-2xl text-slate-500 mb-3">
          <TrendingUp className="w-8 h-8" />
        </div>
        <h3 className="text-base font-medium text-slate-300">No Score History Available</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Perform matching analyses across your resume versions to visualize score evolution over time.
        </p>
      </div>
    );
  }

  // Format data points for Recharts
  const chartData = scoreTrends.map((item, index) => {
    const dateLabel = new Date(item.created_at).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    });
    return {
      index: index + 1,
      label: `v${item.resume_version} (${dateLabel})`,
      targetTitle: item.target_title,
      analysisType: item.analysis_type === 'JOB_MATCH' ? 'Job Match' : 'Career Compatibility',
      atsScore: item.ats_readiness_score,
      compatibilityScore: item.compatibility_score,
      requiredCoverage: item.required_skill_coverage,
    };
  });

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-indigo-400" />
            Score Trajectory Across Iterations
          </h3>
          <p className="text-xs text-slate-400">
            Chronological ATS readiness and compatibility trends (Bounded 0–100 scale)
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <Info className="w-3.5 h-3.5" />
          <span>Real scores calculated by backend engine</span>
        </div>
      </div>

      <div className="h-[280px] w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="label"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
            />
            <YAxis
              domain={[0, 100]}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
              ticks={[0, 25, 50, 75, 100]}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 shadow-2xl text-xs space-y-1.5">
                      <p className="font-semibold text-white">{data.label}</p>
                      <p className="text-slate-400">{data.analysisType}: <span className="text-slate-200">{data.targetTitle}</span></p>
                      {data.atsScore !== null && data.atsScore !== undefined && (
                        <p className="text-indigo-400 font-medium">ATS Readiness: {data.atsScore}%</p>
                      )}
                      <p className="text-emerald-400 font-medium">Compatibility: {data.compatibilityScore}%</p>
                      {data.requiredCoverage !== null && data.requiredCoverage !== undefined && (
                        <p className="text-blue-400 font-medium">Required Skill Coverage: {data.requiredCoverage}%</p>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
              iconType="circle"
            />
            <Line
              type="monotone"
              dataKey="atsScore"
              name="ATS Readiness"
              stroke="#818cf8"
              strokeWidth={2.5}
              dot={{ r: 4, fill: '#818cf8' }}
              activeDot={{ r: 6 }}
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="compatibilityScore"
              name="Role Compatibility"
              stroke="#34d399"
              strokeWidth={2.5}
              dot={{ r: 4, fill: '#34d399' }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="requiredCoverage"
              name="Required Skill Coverage"
              stroke="#38bdf8"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              dot={{ r: 3, fill: '#38bdf8' }}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
