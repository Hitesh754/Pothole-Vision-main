import React, { useState } from 'react';
import { RoadSegment, UrgencyStatus } from '../types';
import { ChevronDown, ChevronUp, Car, Thermometer, Clock, Trash2, Zap } from 'lucide-react';

interface MobileRoadCardProps {
  segment: RoadSegment;
  onSelect: (segment: RoadSegment) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  isScheduled?: boolean;
}

export const MobileRoadCard: React.FC<MobileRoadCardProps> = ({ 
  segment, 
  onSelect, 
  onDelete, 
  isScheduled = false 
}) => {
  const [expanded, setExpanded] = useState(false);
  const hasVisualData = !!segment.visualAnalysis;

  const getStatusBadge = (status: UrgencyStatus) => {
    if (isScheduled) return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
    switch (status) {
      case UrgencyStatus.URGENT: return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case UrgencyStatus.MONITOR: return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case UrgencyStatus.STABLE: return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    }
  };

  return (
    <div className="rounded-2xl border border-emerald-900/40 bg-[#0a1f17]/90 shadow-lg mb-3 overflow-hidden transition-all">
      {/* Primary Card View */}
      <div 
        className="p-4 flex items-center justify-between cursor-pointer active:scale-[0.99] transition-transform"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            <span className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${getStatusBadge(segment.status)}`}>
              {isScheduled ? 'Scheduled' : segment.status}
            </span>
            {hasVisualData && (
              <span className="text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Zap size={10} className="text-emerald-400" /> YOLOv8
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-white leading-tight">{segment.name}</h3>
            <span className="text-xs text-slate-400 font-mono">({segment.district})</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className={`text-xl font-black font-mono ${
              segment.urgencyScore >= 70 ? 'text-rose-400' : segment.urgencyScore >= 40 ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              {segment.urgencyScore.toFixed(0)}
            </span>
            <span className="text-[9px] uppercase tracking-wider block font-mono text-slate-400">Score</span>
          </div>
          {expanded ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
        </div>
      </div>

      {/* Collapsible Details */}
      {expanded && (
        <div className="p-4 pt-0 border-t border-emerald-900/30 text-xs font-mono space-y-3 bg-[#06140e]">
          <div className="grid grid-cols-3 gap-2 text-center pt-3">
            <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Traffic</span>
              <strong className="text-white text-xs">{segment.trafficLoad}</strong>
            </div>
            <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Age</span>
              <strong className="text-white text-xs">{segment.ageYears} yrs</strong>
            </div>
            <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Condition</span>
              <strong className="text-emerald-300 text-xs">{segment.surfaceCondition}/10</strong>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              onClick={() => onSelect(segment)}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs"
            >
              Inspect Details
            </button>
            <button
              onClick={(e) => onDelete(segment.id, e)}
              className="text-rose-400 hover:text-rose-300 flex items-center gap-1 text-xs"
            >
              <Trash2 size={13} /> Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
};