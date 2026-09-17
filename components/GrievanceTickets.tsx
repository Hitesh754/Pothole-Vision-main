import React, { useState } from 'react';
import { GrievanceTicket, CivicIssueType } from '../types';
import { 
  FileCheck2, 
  Clock, 
  MapPin, 
  AlertTriangle, 
  CheckCircle2, 
  Calendar, 
  ShieldAlert, 
  ExternalLink,
  Droplets,
  Wind,
  Building2,
  Copy,
  Download,
  Filter,
  Lightbulb,
  ShieldCheck
} from 'lucide-react';

interface GrievanceTicketsProps {
  tickets: GrievanceTicket[];
  onUpdateStatus: (ticketId: string, status: 'Reported' | 'In Review' | 'Scheduled' | 'Repaired') => void;
  onSelectTicket?: (ticket: GrievanceTicket) => void;
}

export const GrievanceTickets: React.FC<GrievanceTicketsProps> = ({ 
  tickets, 
  onUpdateStatus,
  onSelectTicket 
}) => {
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string>('All');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [viewDossierTicket, setViewDossierTicket] = useState<GrievanceTicket | null>(null);

  const copyDossier = (ticket: GrievanceTicket, e: React.MouseEvent) => {
    e.stopPropagation();
    const text = ticket.citizenDossier || `PUBLIC GRIEVANCE REGISTRATION
Registration ID: ${ticket.govtRegistrationId || ticket.ticketId}
Portal: ${ticket.govtPortal || 'CPGRAMS'}
Location: ${ticket.roadName}, ${ticket.district}
Severity: ${ticket.severityScore}/100`;
    navigator.clipboard.writeText(text);
    setCopiedId(ticket.ticketId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStatusBadge = (status: GrievanceTicket['status']) => {
    switch (status) {
      case 'Reported':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'In Review':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      case 'Scheduled':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      case 'Repaired':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    }
  };

  const getSeverityBadge = (score: number) => {
    if (score >= 70) return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    if (score >= 40) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
  };

  const getPortalBadge = (portal?: string) => {
    if (portal?.includes('NHAI')) {
      return 'bg-orange-950/80 text-orange-300 border-orange-500/40';
    }
    if (portal?.includes('MoHUA') || portal?.includes('Urban')) {
      return 'bg-sky-950/80 text-sky-300 border-sky-500/40';
    }
    return 'bg-purple-950/80 text-purple-300 border-purple-500/40';
  };

  const filteredTickets = selectedCategoryFilter === 'All'
    ? tickets
    : tickets.filter(t => (t.issueCategory || 'Pothole & Crater') === selectedCategoryFilter);

  if (tickets.length === 0) {
    return (
      <div className="bg-[#0a1f17]/80 rounded-2xl border border-emerald-900/40 p-12 text-center shadow-xl">
        <div className="w-16 h-16 rounded-2xl bg-emerald-950/60 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4 text-emerald-400">
          <FileCheck2 size={32} />
        </div>
        <h3 className="text-xl font-bold text-white mb-2">No Government Grievance Tickets Yet</h3>
        <p className="text-slate-400 text-sm max-w-md mx-auto mb-6 leading-relaxed">
          When citizens scan civic hazards such as road potholes, broken street lights, or open manholes, automated official grievance tickets will be logged here with official Govt of India registration IDs.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-16">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0a1f17]/90 p-6 rounded-2xl border border-emerald-900/40 shadow-xl backdrop-blur-md">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="text-[11px] font-mono uppercase tracking-widest text-emerald-400 px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/30 flex items-center gap-1">
              <Building2 size={12} /> Govt of India Civic Grievance Registry
            </span>
            <span className="text-xs text-slate-400 font-mono">
              {filteredTickets.length} Registered Complaints
            </span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Automated Public Grievance Dispatch Board
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Direct citizen integration with <strong>CPGRAMS (pgportal.gov.in)</strong>, <strong>NHAI Rajmargyatra (nhai.gov.in)</strong>, and <strong>Swachhata-MoHUA (sbmurban.org)</strong>.
          </p>
        </div>

        {/* Quick Stats Pill */}
        <div className="flex items-center gap-3 bg-[#06140e] px-4 py-2.5 rounded-xl border border-emerald-900/40 text-xs font-mono">
          <div className="text-center px-2 border-r border-emerald-900/40">
            <span className="block text-amber-400 font-bold text-sm">
              {tickets.filter(t => t.status === 'Reported').length}
            </span>
            <span className="text-slate-400 text-[10px]">Registered</span>
          </div>
          <div className="text-center px-2 border-r border-emerald-900/40">
            <span className="block text-blue-400 font-bold text-sm">
              {tickets.filter(t => t.status === 'In Review' || t.status === 'Scheduled').length}
            </span>
            <span className="text-slate-400 text-[10px]">Under Action</span>
          </div>
          <div className="text-center px-2">
            <span className="block text-emerald-400 font-bold text-sm">
              {tickets.filter(t => t.status === 'Repaired').length}
            </span>
            <span className="text-slate-400 text-[10px]">Rectified</span>
          </div>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap items-center gap-2 bg-[#06140e] p-3 rounded-xl border border-emerald-900/40">
        <span className="text-xs font-mono text-slate-400 mr-2 flex items-center gap-1">
          <Filter size={13} className="text-emerald-400" /> Filter by Hazard:
        </span>
        {['All', 'Pothole & Crater', 'Broken Street Light', 'Open Manhole', 'Road Fissure & Crack'].map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategoryFilter(cat)}
            className={`px-3 py-1 rounded-lg text-xs font-mono transition-all ${
              selectedCategoryFilter === cat
                ? 'bg-emerald-600 text-white font-bold'
                : 'bg-emerald-950/40 text-slate-400 hover:text-white border border-emerald-900/30'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Ticket Cards Grid */}
      <div className="grid md:grid-cols-2 gap-5">
        {filteredTickets.map((ticket) => (
          <div 
            key={ticket.ticketId}
            className="bg-[#0a1f17]/80 rounded-2xl border border-emerald-900/40 overflow-hidden shadow-xl hover:border-emerald-500/40 transition-all group flex flex-col justify-between"
          >
            {/* Top Bar */}
            <div className="p-5 border-b border-emerald-900/30">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-mono font-bold text-emerald-300 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/30">
                      {ticket.govtRegistrationId || ticket.ticketId}
                    </span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getPortalBadge(ticket.govtPortal)}`}>
                      {ticket.govtPortal || 'CPGRAMS (MoRTH)'}
                    </span>
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${getStatusBadge(ticket.status)}`}>
                      {ticket.status}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-white mt-2.5 group-hover:text-emerald-300 transition-colors">
                    {ticket.roadName}
                  </h3>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1">
                    <span className="flex items-center gap-1">
                      <MapPin size={13} className="text-emerald-400" />
                      {ticket.district}
                    </span>
                    <span className="flex items-center gap-1 font-mono text-[11px]">
                      <Calendar size={13} className="text-slate-400" />
                      {new Date(ticket.createdAt).toLocaleDateString()}
                    </span>
                    {ticket.slaDays && (
                      <span className="flex items-center gap-1 font-mono text-[11px] text-amber-400">
                        <Clock size={12} />
                        SLA: {ticket.slaDays} Days
                      </span>
                    )}
                  </div>
                </div>

                {/* Severity Metric */}
                <div className={`px-3 py-1.5 rounded-xl border text-center font-mono shrink-0 ${getSeverityBadge(ticket.severityScore)}`}>
                  <span className="text-lg font-extrabold block leading-tight">
                    {ticket.severityScore}
                  </span>
                  <span className="text-[9px] uppercase tracking-wider font-semibold">Severity</span>
                </div>
              </div>

              {/* Nodal Authority Banner */}
              <div className="p-2.5 rounded-xl bg-[#06140e] border border-emerald-900/30 mt-3 text-xs font-mono">
                <span className="text-slate-400 text-[10px] uppercase tracking-wider block">Assigned Nodal Authority:</span>
                <span className="text-slate-200 text-[11px] font-semibold block truncate">
                  {ticket.nodalAuthority || 'Ministry of Road Transport & Highways - State PWD Wing'}
                </span>
              </div>

              {/* Damage & GPS tags */}
              <div className="flex flex-wrap items-center gap-1.5 mt-3">
                <span className="text-[11px] font-mono bg-rose-950/60 text-rose-300 border border-rose-500/30 px-2 py-0.5 rounded-md">
                  {ticket.issueCategory || 'Pothole & Crater'}
                </span>
                {ticket.damageTypes.map((dt, idx) => (
                  <span key={idx} className="text-[11px] font-mono bg-emerald-950/60 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-md">
                    {dt}
                  </span>
                ))}
                {ticket.gpsCoordinates && (
                  <span className="text-[11px] font-mono bg-slate-900 text-slate-400 border border-slate-700 px-2 py-0.5 rounded-md">
                    GPS: {ticket.gpsCoordinates.lat.toFixed(4)}, {ticket.gpsCoordinates.lng.toFixed(4)}
                  </span>
                )}
              </div>
            </div>

            {/* Middle Section: Image preview & Environmental Impact */}
            <div className="p-5 space-y-4">
              {ticket.imageUrl && (
                <div className="relative rounded-xl overflow-hidden border border-emerald-900/40 aspect-video max-h-48 bg-black flex items-center justify-center">
                  <img 
                    src={ticket.imageUrl} 
                    alt={`Detection for ${ticket.ticketId}`} 
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute bottom-2 left-2 bg-black/80 px-2 py-0.5 rounded text-[10px] font-mono text-emerald-400 border border-emerald-500/30">
                    AI Annotated Evidence
                  </div>
                </div>
              )}

              {/* Environmental Monitoring Banner */}
              {ticket.environmentalImpact && (
                <div className="p-3 bg-[#06140e] rounded-xl border border-emerald-900/30 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <Droplets size={14} className="text-blue-400" />
                    <span className="text-slate-400 text-[11px]">Water-Logging:</span>
                    <span className={`font-bold font-mono ${
                      ticket.environmentalImpact.waterLoggingRisk === 'High' ? 'text-rose-400' : 'text-amber-400'
                    }`}>
                      {ticket.environmentalImpact.waterLoggingRisk}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Wind size={14} className="text-emerald-400" />
                    <span className="text-slate-400 text-[11px]">Dust Index:</span>
                    <span className="font-mono text-emerald-300 font-bold text-[11px]">
                      {ticket.environmentalImpact.dustPollutionScore.split(' ')[0]}
                    </span>
                  </div>
                </div>
              )}

              {/* Official Action Bar (Track on Govt Portal & Copy Dossier) */}
              <div className="flex items-center gap-2 pt-1">
                <a
                  href={ticket.officialPortalUrl || 'https://pgportal.gov.in'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 py-2 px-3 rounded-xl bg-emerald-950/80 hover:bg-emerald-900/80 text-emerald-300 hover:text-white border border-emerald-500/40 text-xs font-mono font-medium flex items-center justify-center gap-1.5 transition-colors"
                >
                  <ExternalLink size={13} />
                  <span>Open Official Govt Portal</span>
                </a>

                <button
                  onClick={(e) => copyDossier(ticket, e)}
                  className="py-2 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 text-xs font-mono font-medium flex items-center justify-center gap-1.5 transition-colors"
                  title="Copy Grievance Dossier"
                >
                  <Copy size={13} />
                  <span>{copiedId === ticket.ticketId ? 'Copied!' : 'Dossier'}</span>
                </button>

                <button
                  onClick={() => setViewDossierTicket(ticket)}
                  className="py-2 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 text-xs font-mono font-medium flex items-center justify-center gap-1 transition-colors"
                  title="View Details"
                >
                  <span>View</span>
                </button>
              </div>
            </div>

            {/* Bottom Controls: Authority Status Transition */}
            <div className="p-4 bg-[#071710] border-t border-emerald-900/30 flex items-center justify-between gap-3">
              <span className="text-[11px] font-mono text-slate-400">Update Authority Status:</span>
              <div className="flex items-center gap-1.5">
                {(['Reported', 'In Review', 'Scheduled', 'Repaired'] as const).map((s) => (
                  <button
                    key={s}
                    onClick={() => onUpdateStatus(ticket.ticketId, s)}
                    className={`px-2 py-1 rounded-lg text-[10px] font-bold font-mono transition-all ${
                      ticket.status === s
                        ? 'bg-emerald-600 text-white shadow-sm'
                        : 'bg-emerald-950/60 text-slate-400 hover:text-white hover:bg-emerald-900/40 border border-emerald-900/40'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Citizen Grievance Dossier Modal */}
      {viewDossierTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-[#0a1f17] rounded-3xl border border-emerald-500/50 shadow-2xl w-full max-w-xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-emerald-900/40 flex justify-between items-start bg-[#06140e]">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/30">
                  Official Public Grievance Dossier
                </span>
                <h3 className="text-lg font-bold text-white mt-1">
                  Registration ID: {viewDossierTicket.govtRegistrationId || viewDossierTicket.ticketId}
                </h3>
              </div>
              <button 
                onClick={() => setViewDossierTicket(null)}
                className="p-1.5 rounded-full hover:bg-emerald-900/40 text-slate-400 hover:text-white transition-colors text-sm font-mono"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto font-mono text-xs text-slate-300">
              <pre className="p-4 rounded-xl bg-black/60 border border-emerald-900/40 whitespace-pre-wrap leading-relaxed">
                {viewDossierTicket.citizenDossier || `PUBLIC GRIEVANCE DOSSIER (GOVERNMENT OF INDIA)
--------------------------------------------------
Registration ID: ${viewDossierTicket.govtRegistrationId || viewDossierTicket.ticketId}
Portal: ${viewDossierTicket.govtPortal || 'CPGRAMS'}
Nodal Authority: ${viewDossierTicket.nodalAuthority || 'State Public Works Department'}
Category: ${viewDossierTicket.issueCategory || 'Pothole & Crater'}
Location: ${viewDossierTicket.roadName}, ${viewDossierTicket.district}
Severity Score: ${viewDossierTicket.severityScore}/100
Statutory Provision: Motor Vehicles Act 1988 (Section 198A) & MoHUA Citizen Charter.`}
              </pre>

              <div className="flex items-center gap-3 pt-2">
                <a
                  href={viewDossierTicket.officialPortalUrl || 'https://pgportal.gov.in'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-center flex items-center justify-center gap-2 shadow-lg transition-all"
                >
                  <ExternalLink size={15} />
                  <span>Open {viewDossierTicket.govtPortal?.split(' ')[0] || 'CPGRAMS'} Portal</span>
                </a>
                <button
                  onClick={(e) => copyDossier(viewDossierTicket, e)}
                  className="px-4 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 transition-all flex items-center gap-1.5"
                >
                  <Copy size={15} />
                  <span>{copiedId === viewDossierTicket.ticketId ? 'Copied!' : 'Copy Dossier'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

