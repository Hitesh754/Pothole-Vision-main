import React from 'react';
import { RoadSegment, UrgencyStatus, MaintenanceStatus } from '../types';
import { 
  AlertCircle, 
  CheckCircle, 
  HelpCircle, 
  ArrowUpRight, 
  Clock, 
  ClipboardCheck, 
  Trash2, 
  Zap, 
  Activity 
} from 'lucide-react';

interface RoadTableProps {
  segments: RoadSegment[];
  onSelectSegment: (segment: RoadSegment) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  scheduledIds?: Set<string>;
}

export const RoadTable: React.FC<RoadTableProps> = ({ 
  segments, 
  onSelectSegment, 
  onDelete, 
  scheduledIds = new Set() 
}) => {
  const getStatusColor = (status: UrgencyStatus, isScheduled: boolean) => {
    if (isScheduled) return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
    switch (status) {
      case UrgencyStatus.URGENT: return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case UrgencyStatus.MONITOR: return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case UrgencyStatus.STABLE: return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      default: return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const getStatusIcon = (status: UrgencyStatus, isScheduled: boolean) => {
    if (isScheduled) return <Clock size={14} />;
    switch (status) {
      case UrgencyStatus.URGENT: return <AlertCircle size={14} />;
      case UrgencyStatus.MONITOR: return <HelpCircle size={14} />;
      case UrgencyStatus.STABLE: return <CheckCircle size={14} />;
    }
  };

  if (segments.length === 0) {
    return (
      <div className="bg-[#0a1f17]/80 rounded-2xl shadow-xl border border-emerald-900/40 p-12 text-center text-slate-400">
        <ClipboardCheck className="mx-auto h-12 w-12 text-emerald-500/40 mb-3" />
        <h3 className="text-lg font-bold text-white mb-1">No Road Records Found</h3>
        <p className="text-xs">Adjust your district filter or scan new road segments.</p>
      </div>
    );
  }

  return (
    <div className="hidden md:block bg-[#0a1f17]/90 rounded-2xl shadow-xl border border-emerald-900/40 overflow-hidden backdrop-blur-md">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-[#071710] border-b border-emerald-900/40 font-mono text-xs uppercase tracking-wider text-emerald-400">
            <tr>
              <th className="px-6 py-4">Road Segment</th>
              <th className="px-6 py-4">District</th>
              <th className="px-6 py-4">Traffic / Age / Weather</th>
              <th className="px-6 py-4">Surface</th>
              <th className="px-6 py-4 text-right">Urgency</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Repair Lifecycle</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-emerald-950/60 font-sans">
            {segments.map((segment) => {
              const isScheduled = scheduledIds.has(segment.id);
              const hasVisualData = !!segment.visualAnalysis;

              const progressValue = segment.progress ?? (
                segment.surfaceCondition > 8 ? 100 : 
                isScheduled ? 65 : 
                hasVisualData ? 35 : 12
              );

              return (
                <tr 
                  key={segment.id} 
                  className={`transition-colors cursor-pointer group ${
                    isScheduled 
                      ? 'bg-purple-950/20 hover:bg-purple-950/40' 
                      : 'hover:bg-emerald-950/30'
                  }`}
                  onClick={() => onSelectSegment(segment)}
                >
                  <td className="px-6 py-4 font-bold text-white">
                    <div className="flex items-center gap-2">
                      <span className="group-hover:text-emerald-300 transition-colors">
                        {segment.name}
                      </span>
                      {hasVisualData && (
                        <span className="text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40 px-1.5 py-0.5 rounded flex items-center gap-1">
                          <Zap size={10} className="text-emerald-400" /> YOLOv8
                        </span>
                      )}
                    </div>
                  </td>

                  <td className="px-6 py-4 text-xs font-mono text-slate-300">
                    {segment.district}
                  </td>

                  <td className="px-6 py-4 text-xs text-slate-400 font-mono">
                    <div className="flex flex-col gap-0.5">
                      <span>Trf: <strong className="text-slate-200">{segment.trafficLoad}</strong></span>
                      <span>Age: <strong className="text-slate-200">{segment.ageYears} yrs</strong></span>
                      <span>Wthr: <strong className="text-slate-200">{segment.weatherImpact}</strong></span>
                    </div>
                  </td>

                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span className={`font-mono font-bold ${segment.surfaceCondition < 5 ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {segment.surfaceCondition}
                      </span>
                      <span className="text-xs text-slate-500">/10</span>
                    </div>
                    <div className="w-20 h-1.5 bg-slate-800 rounded-full mt-1.5 overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${
                          segment.surfaceCondition < 4 ? 'bg-rose-500' : segment.surfaceCondition < 7 ? 'bg-amber-500' : 'bg-emerald-500'
                        }`} 
                        style={{ width: `${segment.surfaceCondition * 10}%` }}
                      />
                    </div>
                  </td>

                  <td className="px-6 py-4 text-right">
                    <span className={`font-mono font-black text-lg ${
                      segment.urgencyScore >= 70 ? 'text-rose-400' : segment.urgencyScore >= 40 ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {segment.urgencyScore.toFixed(0)}
                    </span>
                  </td>

                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-semibold border ${getStatusColor(segment.status, isScheduled)}`}>
                      {getStatusIcon(segment.status, isScheduled)}
                      {isScheduled ? 'Scheduled' : segment.status}
                    </span>
                  </td>

                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1 w-24">
                      <div className="flex justify-between text-[10px] font-mono items-center">
                        <span className="text-slate-300 font-bold">{progressValue}%</span>
                        <span className="text-slate-500 capitalize">
                          {progressValue === 100 ? 'Fixed' : progressValue > 60 ? 'Repair' : 'Queue'}
                        </span>
                      </div>
                      <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${
                            progressValue === 100 ? 'bg-emerald-500' : progressValue > 60 ? 'bg-purple-500' : 'bg-slate-500'
                          }`}
                          style={{ width: `${progressValue}%` }}
                        />
                      </div>
                    </div>
                  </td>

                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={(e) => onDelete(segment.id, e)}
                      className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 rounded-lg transition-colors"
                      title="Delete Record"
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};