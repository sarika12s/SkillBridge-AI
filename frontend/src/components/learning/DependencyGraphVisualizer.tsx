import React, { useMemo, useState } from 'react';
import type { LearningPathGraph, LearningPathGraphNode } from '../../types/learning';
import { Info } from 'lucide-react';

interface DependencyGraphVisualizerProps {
  graph?: LearningPathGraph;
}

export const DependencyGraphVisualizer: React.FC<DependencyGraphVisualizerProps> = ({
  graph,
}) => {
  const [selectedNode, setSelectedNode] = useState<LearningPathGraphNode | null>(null);

  // Group nodes by stage
  const { stages, nodePositions, svgDimensions } = useMemo(() => {
    if (!graph || !graph.nodes || graph.nodes.length === 0) {
      return { stages: {}, nodePositions: {}, svgDimensions: { width: 800, height: 400 } };
    }

    const stagesMap: Record<number, LearningPathGraphNode[]> = {};
    graph.nodes.forEach((node) => {
      const stg = node.stage ?? 1;
      if (!stagesMap[stg]) stagesMap[stg] = [];
      stagesMap[stg].push(node);
    });

    const stageKeys = Object.keys(stagesMap)
      .map(Number)
      .sort((a, b) => a - b);

    // Calculate node coordinates for SVG
    const colWidth = 240;
    const rowHeight = 100;
    const startX = 60;
    const startY = 80;

    const positions: Record<string, { x: number; y: number }> = {};
    let maxNodesInCol = 1;

    stageKeys.forEach((stg, colIdx) => {
      const nodesInStage = stagesMap[stg];
      maxNodesInCol = Math.max(maxNodesInCol, nodesInStage.length);
      nodesInStage.forEach((node, rowIdx) => {
        positions[node.id] = {
          x: startX + colIdx * colWidth,
          y: startY + rowIdx * rowHeight,
        };
      });
    });

    const width = Math.max(800, startX + stageKeys.length * colWidth + 60);
    const height = Math.max(450, startY + maxNodesInCol * rowHeight + 80);

    return {
      stages: stagesMap,
      nodePositions: positions,
      svgDimensions: { width, height },
    };
  }, [graph]);

  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-2xl text-slate-400">
        <Info className="w-8 h-8 text-slate-500 mx-auto mb-2" />
        <p className="text-sm">No dependency graph available for this learning pathway.</p>
      </div>
    );
  }

  const getNodeColor = (status: string) => {
    switch (status) {
      case 'ACQUIRED':
        return {
          bg: '#064e3b',
          border: '#10b981',
          text: '#a7f3d0',
          badge: 'ACQUIRED',
        };
      case 'COMPLETED':
        return {
          bg: '#065f46',
          border: '#34d399',
          text: '#d1fae5',
          badge: 'COMPLETED',
        };
      case 'IN_PROGRESS':
        return {
          bg: '#1e3a8a',
          border: '#60a5fa',
          text: '#dbeafe',
          badge: 'LEARNING',
        };
      default:
        return {
          bg: '#1e293b',
          border: '#475569',
          text: '#cbd5e1',
          badge: 'PLANNED',
        };
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6">
      {/* Header and Legend */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4 mb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <span>Skill Dependency Directed Acyclic Graph (DAG)</span>
          </h3>
          <p className="text-xs text-slate-400">
            Visual topological ordering ensuring core prerequisites unlock dependent technologies.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500/20 border border-emerald-500" />
            <span className="text-slate-300">Acquired / Done</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-blue-500/20 border border-blue-500" />
            <span className="text-slate-300">In Progress</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-slate-800 border border-slate-600" />
            <span className="text-slate-400">Planned Stage</span>
          </div>
        </div>
      </div>

      {/* SVG Container with horizontal scroll */}
      <div className="overflow-x-auto overflow-y-auto max-h-[500px] border border-slate-800/80 rounded-xl bg-slate-950/70 p-4">
        <svg
          width={svgDimensions.width}
          height={svgDimensions.height}
          className="select-none"
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="10"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="#6366f1" opacity="0.8" />
            </marker>
          </defs>

          {/* Render Stage Column Headers */}
          {Object.keys(stages).map((stgKey, idx) => {
            const stgNum = Number(stgKey);
            const x = 60 + idx * 240;
            const stageLabel =
              stgNum === 0
                ? 'Candidate Baseline (Acquired)'
                : `Stage ${stgNum}: ${
                    stgNum === 1
                      ? 'Foundations'
                      : stgNum === 2
                      ? 'Core Frameworks'
                      : 'Advanced Ecosystem'
                  }`;

            return (
              <g key={`header-${stgNum}`}>
                <text
                  x={x + 85}
                  y={35}
                  textAnchor="middle"
                  fill="#94a3b8"
                  fontSize="12"
                  fontWeight="bold"
                >
                  {stageLabel}
                </text>
                <line
                  x1={x - 20}
                  y1={45}
                  x2={x + 190}
                  y2={45}
                  stroke="#334155"
                  strokeDasharray="4"
                />
              </g>
            );
          })}

          {/* Render Prerequisite Edges */}
          {graph.edges?.map((edge, idx) => {
            const src = nodePositions[edge.source];
            const tgt = nodePositions[edge.target];
            if (!src || !tgt) return null;

            // Box width = 170, height = 55
            const x1 = src.x + 170;
            const y1 = src.y + 27;
            const x2 = tgt.x;
            const y2 = tgt.y + 27;

            // Bezier curve control points
            const dx = Math.max(30, (x2 - x1) * 0.5);
            const pathData = `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2 - 10} ${y2}`;

            return (
              <path
                key={`edge-${idx}`}
                d={pathData}
                fill="none"
                stroke="#6366f1"
                strokeWidth="2"
                strokeOpacity="0.6"
                markerEnd="url(#arrowhead)"
              />
            );
          })}

          {/* Render Nodes */}
          {graph.nodes?.map((node) => {
            const pos = nodePositions[node.id];
            if (!pos) return null;

            const styling = getNodeColor(node.status);
            const isSelected = selectedNode?.id === node.id;

            return (
              <g
                key={`node-${node.id}`}
                transform={`translate(${pos.x}, ${pos.y})`}
                className="cursor-pointer transition-transform hover:scale-105"
                onClick={() => setSelectedNode(node)}
              >
                {/* Node Box */}
                <rect
                  width="170"
                  height="55"
                  rx="10"
                  ry="10"
                  fill={styling.bg}
                  stroke={isSelected ? '#f43f5e' : styling.border}
                  strokeWidth={isSelected ? '2.5' : '1.5'}
                />

                {/* Status Badge Tag */}
                <rect
                  x="8"
                  y="8"
                  width="70"
                  height="14"
                  rx="4"
                  fill="#0f172a"
                  opacity="0.8"
                />
                <text
                  x="43"
                  y="18"
                  textAnchor="middle"
                  fill={styling.text}
                  fontSize="8"
                  fontWeight="bold"
                >
                  {styling.badge}
                </text>

                {/* Skill Name */}
                <text
                  x="12"
                  y="38"
                  fill="#f8fafc"
                  fontSize="12"
                  fontWeight="bold"
                >
                  {node.label.length > 18 ? node.label.slice(0, 16) + '...' : node.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected Node Details Box */}
      {selectedNode && (
        <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 block mb-0.5">Selected Competency</span>
            <span className="text-sm font-bold text-slate-100">{selectedNode.label}</span>
            <span className="text-xs text-slate-400 ml-2">({selectedNode.status})</span>
          </div>
          <button
            onClick={() => setSelectedNode(null)}
            className="text-xs text-slate-500 hover:text-slate-300 transition"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};
