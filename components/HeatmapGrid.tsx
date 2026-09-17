import React from 'react';
import { RoadSegment } from '../types';
import { MapPin, ShieldAlert, Layers } from 'lucide-react';

interface HeatmapGridProps {
  segments: RoadSegment[];
  onSelectSegment: (id: string) => void;
}

export const HeatmapGrid: React.FC<HeatmapGridProps> = ({ segments, onSelectSegment }) => {
  const getColor = (score: number) => {
    if (score < 40) return `bg-emerald-500/80 border-emerald-400 text-white shadow-[0_0_12px_rgba(16,185,129,0.3)]`;
    if (score < 60) return `bg-amber-500/80 border-amber-400 text-white shadow-[0_0_12px_rgba(245,158,11,0.3)]`;
    if (score < 80) return `bg-orange-500/80 border-orange-400 text-white shadow-[0_0_12px_rgba(249,115,22,0.3)]`;
    return `bg-rose-600 border-rose-400 text-white shadow-[0_0_15px_rgba(225,29,72,0.4)] animate-pulse`;
  };

  // Group segments by district
  const groupedSegments = segments.reduce((acc, segment) => {
    if (!acc[segment.district]) {
      acc[segment.district] = [];
    }
    acc[segment.district].push(segment);
    return acc;
  }, {} as Record<string, RoadSegment[]>);

  const districts = Object.keys(groupedSegments).sort();

  return (
    <div className="w-full space-y-6 animate-in fade-in duration-500 pb-20">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0a1f17]/90 p-6 rounded-2xl border border-emerald-900/40 shadow-xl backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono uppercase tracking-widest text-emerald-400 px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/30">
              Geospatial Distribution
            </span>
          </div>
          <h3 className="text-2xl font-bold text-white flex items-center gap-2 tracking-tight">
            <MapPin size={22} className="text-emerald-400" />
            Zone Infrastructure Urgency Heatmap
          </h3>
          <p className="text-slate-400 text-xs mt-1">
            Visual breakdown of civil road structural stress & pothole density across administrative zones.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-2 text-xs bg-[#06140e] p-2.5 rounded-xl border border-emerald-900/40 font-mono">
          <div className="flex items-center gap-1.5 text-slate-300">
            <div className="w-3 h-3 bg-emerald-500 rounded-sm" /> Stable (&lt;40)
          </div>
          <div className="flex items-center gap-1.5 text-slate-300">
            <div className="w-3 h-3 bg-amber-500 rounded-sm" /> Monitor (40-60)
          </div>
          <div className="flex items-center gap-1.5 text-slate-300">
            <div className="w-3 h-3 bg-orange-500 rounded-sm" /> Warning (60-80)
          </div>
          <div className="flex items-center gap-1.5 text-slate-300">
            <div className="w-3 h-3 bg-rose-600 rounded-sm" /> Critical (80+)
          </div>
        </div>
      </div>

      {/* Grid of Districts */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {districts.map((district) => {
          const districtSegments = groupedSegments[district];
          const avgScore = districtSegments.reduce((acc, s) => acc + s.urgencyScore, 0) / districtSegments.length;

          return (
            <div 
              key={district} 
              className="bg-[#0a1f17]/80 rounded-2xl border border-emerald-900/40 shadow-xl overflow-hidden flex flex-col hover:border-emerald-500/40 transition-all"
            >
              <div className="p-4 border-b border-emerald-900/30 flex justify-between items-center bg-[#071710]">
                <h4 className="font-bold text-white text-sm tracking-wide">{district}</h4>
                <div className="text-xs font-mono">
                  <span className="text-slate-400">Mean Index: </span>
                  <span className={`${avgScore >= 60 ? 'text-rose-400' : 'text-emerald-400'} font-bold`}>
                    {avgScore.toFixed(0)}
                  </span>
                </div>
              </div>

              <div className="p-5 flex-1">
                <div className="grid grid-cols-5 gap-2.5">
                  {districtSegments.map((segment) => (
                    <div
                      key={segment.id}
                      onClick={() => onSelectSegment(segment.id)}
                      className={`
                        aspect-square rounded-xl cursor-pointer transition-all duration-200 hover:scale-110 relative group border
                        ${getColor(segment.urgencyScore)}
                        flex items-center justify-center
                      `}
                    >
                      {/* Urgency Number Inside Tile */}
                      <span className="text-[11px] font-bold font-mono">
                        {segment.urgencyScore.toFixed(0)}
                      </span>

                      {/* Tooltip */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[140px] bg-[#06140e] text-white text-xs p-2.5 rounded-xl shadow-2xl pointer-events-none opacity-0 group-hover:opacity-100 z-50 transition-all scale-95 group-hover:scale-100 origin-bottom border border-emerald-500/40 backdrop-blur-md">
                        <div className="font-bold truncate text-center mb-0.5 text-white">{segment.name}</div>
                        <div className={`text-center font-mono text-[10px] font-semibold ${segment.urgencyScore >= 70 ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {segment.status}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};