import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { Layout } from './components/Layout';
import { RoadTable } from './components/RoadTable';
import { MobileRoadCard } from './components/MobileRoadCard';
import { HeatmapGrid } from './components/HeatmapGrid';
import { VisualInspection } from './components/VisualInspection';
import { GrievanceTickets } from './components/GrievanceTickets';
import { TeamModal } from './components/TeamModal';
import { 
  RoadSegment, 
  TrafficLoad, 
  WeatherImpact, 
  UrgencyStatus, 
  VisualAnalysis,
  GrievanceTicket,
  MaintenanceStatus
} from './types';
import { generateMaintenanceReport, analyzeLocationConditions, LocationContext } from './services/mlService';
import { supabase } from './services/supabaseClient';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell 
} from 'recharts';
import { 
  Activity, 
  Sparkles, 
  RefreshCw, 
  ArrowRight, 
  X, 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  Database, 
  Trash2, 
  Filter, 
  Settings2, 
  AlertTriangle, 
  CalendarCheck, 
  Clock, 
  Zap, 
  Radio, 
  Loader2, 
  Signal, 
  Plus, 
  Save, 
  Cpu,
  Leaf,
  FileCheck2,
  Droplets,
  AlertOctagon
} from 'lucide-react';

// --- Static Data ---
const INDIAN_ZONES = ['Zone 1 (North)', 'Zone 2 (South)', 'Ward 10', 'Ind. Estate', 'Old City', 'Tech Corridor'];

const INITIAL_SEED_SEGMENTS: RoadSegment[] = [
  {
    id: 'seg-001',
    name: 'MG Road Expressway',
    district: 'Zone 1 (North)',
    trafficLoad: TrafficLoad.HIGH,
    ageYears: 7,
    weatherImpact: WeatherImpact.SEVERE,
    surfaceCondition: 3,
    urgencyScore: 84,
    status: UrgencyStatus.URGENT,
    progress: 35,
    visualAnalysis: {
      potholeCount: 3,
      severityScore: 82,
      damageType: ['Severe Pothole', 'Asphalt Crater'],
      processedAt: new Date().toISOString(),
      environmentalImpact: {
        waterLoggingRisk: 'High',
        dustPollutionScore: 'PM10 +68%',
        soilErosionHazard: 'Accelerated Runoff'
      }
    }
  },
  {
    id: 'seg-002',
    name: 'Outer Ring Road (Flyover Approach)',
    district: 'Tech Corridor',
    trafficLoad: TrafficLoad.EXTREME,
    ageYears: 4,
    weatherImpact: WeatherImpact.MODERATE,
    surfaceCondition: 5,
    urgencyScore: 68,
    status: UrgencyStatus.MONITOR,
    progress: 60,
    visualAnalysis: {
      potholeCount: 1,
      severityScore: 62,
      damageType: ['Longitudinal Crack'],
      processedAt: new Date().toISOString(),
      environmentalImpact: {
        waterLoggingRisk: 'Moderate',
        dustPollutionScore: 'PM10 +25%',
        soilErosionHazard: 'Contained'
      }
    }
  },
  {
    id: 'seg-003',
    name: 'Station Junction Road',
    district: 'Zone 2 (South)',
    trafficLoad: TrafficLoad.EXTREME,
    ageYears: 11,
    weatherImpact: WeatherImpact.SEVERE,
    surfaceCondition: 2,
    urgencyScore: 92,
    status: UrgencyStatus.URGENT,
    progress: 15,
    visualAnalysis: {
      potholeCount: 4,
      severityScore: 91,
      damageType: ['Severe Pothole', 'Alligator Cracking'],
      processedAt: new Date().toISOString(),
      environmentalImpact: {
        waterLoggingRisk: 'High',
        dustPollutionScore: 'PM10 +88%',
        soilErosionHazard: 'Accelerated Runoff'
      }
    }
  },
  {
    id: 'seg-004',
    name: 'Industrial Corridor Sector 4',
    district: 'Ind. Estate',
    trafficLoad: TrafficLoad.HIGH,
    ageYears: 8,
    weatherImpact: WeatherImpact.MODERATE,
    surfaceCondition: 4,
    urgencyScore: 74,
    status: UrgencyStatus.URGENT,
    progress: 45
  },
  {
    id: 'seg-005',
    name: 'Heritage Market Lane',
    district: 'Old City',
    trafficLoad: TrafficLoad.MEDIUM,
    ageYears: 3,
    weatherImpact: WeatherImpact.MILD,
    surfaceCondition: 8,
    urgencyScore: 32,
    status: UrgencyStatus.STABLE,
    progress: 100
  },
  {
    id: 'seg-006',
    name: 'Ward 10 Residential Bypass',
    district: 'Ward 10',
    trafficLoad: TrafficLoad.LOW,
    ageYears: 2,
    weatherImpact: WeatherImpact.MILD,
    surfaceCondition: 9,
    urgencyScore: 24,
    status: UrgencyStatus.STABLE,
    progress: 100
  }
];

const INITIAL_SEED_TICKETS: GrievanceTicket[] = [
  {
    ticketId: 'RS-2026-9438',
    govtRegistrationId: 'MORTE/E/2026/0048192',
    govtPortal: 'CPGRAMS (MoRTH - Ministry of Road Transport)',
    nodalAuthority: 'Ministry of Road Transport & Highways - State PWD Wing',
    officialPortalUrl: 'https://pgportal.gov.in',
    slaDays: 15,
    issueCategory: 'Pothole & Crater',
    segmentId: 'seg-001',
    roadName: 'MG Road Expressway',
    district: 'Zone 1 (North)',
    createdAt: new Date(Date.now() - 3600000 * 2).toISOString(),
    status: 'Reported',
    potholeCount: 3,
    severityScore: 82,
    damageTypes: ['Severe Pothole', 'Asphalt Crater'],
    gpsCoordinates: { lat: 28.6139, lng: 77.2090 },
    citizenDossier: `PUBLIC GRIEVANCE DOSSIER (GOVERNMENT OF INDIA)\nRegistration ID: MORTE/E/2026/0048192\nPortal: CPGRAMS (MoRTH)\nTracking Link: https://pgportal.gov.in\nNodal Authority: Ministry of Road Transport & Highways - State PWD Wing\nSLA: 15 Business Days\nCategory: Pothole & Crater\nLocation: MG Road Expressway, Zone 1 (North)\nSeverity: 82/100`,
    environmentalImpact: {
      waterLoggingRisk: 'High',
      dustPollutionScore: 'PM10 +68%',
      soilErosionHazard: 'Accelerated Runoff'
    }
  },
  {
    ticketId: 'RS-2026-7721',
    govtRegistrationId: 'NHAI-RJY-2026-009182',
    govtPortal: 'NHAI Rajmargyatra (National Highways)',
    nodalAuthority: 'National Highways Authority of India (NHAI) - PIU (Delhi-NCR)',
    officialPortalUrl: 'https://nhai.gov.in',
    slaDays: 3,
    issueCategory: 'Pothole & Crater',
    segmentId: 'seg-003',
    roadName: 'Station Junction Road',
    district: 'Zone 2 (South)',
    createdAt: new Date(Date.now() - 3600000 * 24).toISOString(),
    status: 'Scheduled',
    potholeCount: 4,
    severityScore: 91,
    damageTypes: ['Severe Pothole', 'Alligator Cracking'],
    gpsCoordinates: { lat: 28.5355, lng: 77.3910 },
    citizenDossier: `PUBLIC GRIEVANCE DOSSIER (GOVERNMENT OF INDIA)\nRegistration ID: NHAI-RJY-2026-009182\nPortal: NHAI Rajmargyatra\nTracking Link: https://nhai.gov.in\nNodal Authority: NHAI PIU\nSLA: 3 Business Days\nCategory: Pothole & Crater\nLocation: Station Junction Road\nSeverity: 91/100`,
    environmentalImpact: {
      waterLoggingRisk: 'High',
      dustPollutionScore: 'PM10 +88%',
      soilErosionHazard: 'Accelerated Runoff'
    }
  },
  {
    ticketId: 'RS-2026-3810',
    govtRegistrationId: 'MOHUA/E/2026/0073129',
    govtPortal: 'CPGRAMS (MoHUA - Urban Affairs)',
    nodalAuthority: 'Municipal Corporation - Street Lighting & Electrical Division',
    officialPortalUrl: 'https://pgportal.gov.in',
    slaDays: 7,
    issueCategory: 'Broken Street Light',
    segmentId: 'seg-002',
    roadName: 'Outer Ring Road (Flyover Approach)',
    district: 'Tech Corridor',
    createdAt: new Date(Date.now() - 3600000 * 48).toISOString(),
    status: 'In Review',
    potholeCount: 1,
    severityScore: 62,
    damageTypes: ['Defective Street Light Luminaire'],
    gpsCoordinates: { lat: 28.4595, lng: 77.0266 },
    citizenDossier: `PUBLIC GRIEVANCE DOSSIER (GOVERNMENT OF INDIA)\nRegistration ID: MOHUA/E/2026/0073129\nPortal: CPGRAMS (MoHUA)\nTracking Link: https://pgportal.gov.in\nNodal Authority: Municipal Corporation - Street Lighting & Electrical Division\nSLA: 7 Business Days\nCategory: Broken Street Light\nLocation: Outer Ring Road (Flyover Approach)\nSeverity: 62/100`,
    environmentalImpact: {
      waterLoggingRisk: 'Low',
      dustPollutionScore: 'N/A (Pedestrian Safety Risk)',
      soilErosionHazard: 'Electrical Hazard'
    }
  },
  {
    ticketId: 'RS-2026-1104',
    govtRegistrationId: 'SBM-ULB-2026-0038102',
    govtPortal: 'Swachhata-MoHUA (Urban Local Body 311)',
    nodalAuthority: 'Municipal Drainage & Sewerage Board',
    officialPortalUrl: 'https://sbmurban.org',
    slaDays: 3,
    issueCategory: 'Open Manhole',
    segmentId: 'seg-005',
    roadName: 'Heritage Market Lane',
    district: 'Old City',
    createdAt: new Date(Date.now() - 3600000 * 72).toISOString(),
    status: 'Repaired',
    potholeCount: 1,
    severityScore: 95,
    damageTypes: ['Uncovered Manhole Hazard'],
    gpsCoordinates: { lat: 28.6562, lng: 77.2410 },
    citizenDossier: `PUBLIC GRIEVANCE DOSSIER (GOVERNMENT OF INDIA)\nRegistration ID: SBM-ULB-2026-0038102\nPortal: Swachhata-MoHUA 311\nTracking Link: https://sbmurban.org\nNodal Authority: Municipal Drainage Board\nSLA: 3 Business Days\nCategory: Open Manhole\nLocation: Heritage Market Lane\nSeverity: 95/100`,
    environmentalImpact: {
      waterLoggingRisk: 'High',
      dustPollutionScore: 'Sewer Gas Risk (Drain Choking)',
      soilErosionHazard: 'Fall Hazard'
    }
  }
];


const generateSafeUUID = (): string => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    try {
      return crypto.randomUUID();
    } catch (e) {}
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

const calculateUrgency = (
  age: any, 
  traffic: TrafficLoad, 
  weather: WeatherImpact, 
  condition: any,
  visualAnalysis?: VisualAnalysis 
): number => {
  let score = 0;
  const safeAge = typeof age === 'number' ? age : (parseFloat(age) || 0);
  const safeCondition = typeof condition === 'number' ? condition : (parseFloat(condition) || 5);
  
  score += Math.min(safeAge * 2.5, 30);
  const trafficValues = { [TrafficLoad.LOW]: 5, [TrafficLoad.MEDIUM]: 15, [TrafficLoad.HIGH]: 30, [TrafficLoad.EXTREME]: 40 };
  score += (trafficValues[traffic] || 15);
  const weatherValues = { [WeatherImpact.MILD]: 5, [WeatherImpact.MODERATE]: 15, [WeatherImpact.SEVERE]: 30 };
  score += (weatherValues[weather] || 15);
  score += (10 - safeCondition) * 4;

  if (visualAnalysis) {
    const severity = typeof visualAnalysis.severityScore === 'number' ? visualAnalysis.severityScore : 0;
    const count = typeof visualAnalysis.potholeCount === 'number' ? visualAnalysis.potholeCount : 0;
    score += severity * 0.4;
    if (count > 2) score += 15;
  }

  const finalScore = Math.min(Math.max(score, 0), 100);
  return isNaN(finalScore) ? 50 : finalScore;
};

const determineStatus = (score: number): UrgencyStatus => {
  if (score >= 70) return UrgencyStatus.URGENT;
  if (score >= 40) return UrgencyStatus.MONITOR;
  return UrgencyStatus.STABLE;
};

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [rawSegments, setRawSegments] = useState<any[]>([]);
  const [tickets, setTickets] = useState<GrievanceTicket[]>(() => {
    try {
      const saved = localStorage.getItem('roadsense_tickets');
      return saved ? JSON.parse(saved) : INITIAL_SEED_TICKETS;
    } catch (e) {
      return INITIAL_SEED_TICKETS;
    }
  });

  const [isLoading, setIsLoading] = useState(false);
  const [selectedDistrict, setSelectedDistrict] = useState<string>('All');
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [selectedSegment, setSelectedSegment] = useState<RoadSegment | null>(null);
  const [mlReport, setMlReport] = useState<string>('');
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [isScheduling, setIsScheduling] = useState(false);
  const [locationContext, setLocationContext] = useState<LocationContext | null>(null);

  const [scheduledIds, setScheduledIds] = useState<Set<string>>(new Set(['seg-003']));
  const [visualSyncStatus, setVisualSyncStatus] = useState<'idle' | 'syncing' | 'success' | 'error'>('idle');

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Save tickets to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('roadsense_tickets', JSON.stringify(tickets));
    } catch (e) {}
  }, [tickets]);

  // Initial load from Supabase or fallback to seeds
  const fetchSegments = useCallback(async () => {
    try {
      const { data, error } = await supabase.from('road_segments').select('*');
      if (data && data.length > 0) {
        setRawSegments(data);
      } else {
        setRawSegments(INITIAL_SEED_SEGMENTS);
      }
    } catch (err) {
      setRawSegments(INITIAL_SEED_SEGMENTS);
    }
  }, []);

  useEffect(() => {
    fetchSegments();
  }, [fetchSegments]);

  // Process raw data into enriched RoadSegments
  const segments: RoadSegment[] = useMemo(() => {
    const list = rawSegments.length > 0 ? rawSegments : INITIAL_SEED_SEGMENTS;
    return list.map((raw: any) => {
      const urgencyScore = calculateUrgency(
        raw.age_years ?? raw.ageYears,
        raw.traffic_load ?? raw.trafficLoad ?? TrafficLoad.MEDIUM,
        raw.weather_impact ?? raw.weatherImpact ?? WeatherImpact.MODERATE,
        raw.surface_condition ?? raw.surfaceCondition ?? 5,
        raw.visual_analysis ?? raw.visualAnalysis
      );

      return {
        id: raw.id,
        name: raw.name,
        district: raw.district,
        trafficLoad: raw.traffic_load ?? raw.trafficLoad ?? TrafficLoad.MEDIUM,
        ageYears: raw.age_years ?? raw.ageYears ?? 0,
        weatherImpact: raw.weather_impact ?? raw.weatherImpact ?? WeatherImpact.MODERATE,
        surfaceCondition: raw.surface_condition ?? raw.surfaceCondition ?? 5,
        urgencyScore: urgencyScore,
        status: determineStatus(urgencyScore),
        visualAnalysis: raw.visual_analysis ?? raw.visualAnalysis,
        progress: raw.progress ?? (urgencyScore >= 70 ? 25 : urgencyScore >= 40 ? 60 : 100)
      };
    });
  }, [rawSegments]);

  const filteredSegments = useMemo(() => {
    if (selectedDistrict === 'All') return segments;
    return segments.filter((s) => s.district === selectedDistrict);
  }, [selectedDistrict, segments]);

  const openSegmentDetails = (segment: RoadSegment | string) => {
    const seg = typeof segment === 'string' ? segments.find((s) => s.id === segment) : segment;
    if (seg) {
      setSelectedSegment(seg);
      setMlReport('');
    }
  };

  const handleDeleteSegment = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setRawSegments((prev) => prev.filter((s) => s.id !== id));
    if (selectedSegment?.id === id) setSelectedSegment(null);
    showToast('Road segment record deleted.');
  };

  const handleUpdateTicketStatus = (
    ticketId: string, 
    status: 'Reported' | 'In Review' | 'Scheduled' | 'Repaired'
  ) => {
    setTickets((prev) =>
      prev.map((t) => (t.ticketId === ticketId ? { ...t, status } : t))
    );
    showToast(`Ticket ${ticketId} status updated to '${status}'.`);
  };

  // Called when AI Scan completes & user clicks "Raise Official Ticket on Govt Portal"
  const handleVisualAnalysisComplete = async (
    analysis: VisualAnalysis, 
    image: string, 
    segmentId: string,
    govtTicket?: Partial<GrievanceTicket>
  ) => {
    const targetSegment = segments.find((s) => s.id === segmentId) || segments[0];
    
    // 1. Update Segment State
    setRawSegments((prev) =>
      prev.map((s) => (s.id === targetSegment.id ? { ...s, visual_analysis: analysis } : s))
    );

    // 2. Generate Grievance Ticket
    const randomTicketNum = Math.floor(1000 + Math.random() * 9000);
    const newTicketId = `RS-2026-${randomTicketNum}`;
    const regId = govtTicket?.govtRegistrationId || `MORTE/E/2026/00${randomTicketNum}`;
    const portal = govtTicket?.govtPortal || 'CPGRAMS (MoRTH - Ministry of Road Transport)';

    const newTicket: GrievanceTicket = {
      ticketId: newTicketId,
      govtRegistrationId: regId,
      govtPortal: portal,
      nodalAuthority: govtTicket?.nodalAuthority || 'Ministry of Road Transport & Highways - State PWD Wing',
      officialPortalUrl: govtTicket?.officialPortalUrl || 'https://pgportal.gov.in',
      slaDays: govtTicket?.slaDays || 15,
      issueCategory: govtTicket?.issueCategory || analysis.issueCategory || 'Pothole & Crater',
      segmentId: targetSegment.id,
      roadName: targetSegment.name,
      district: targetSegment.district,
      createdAt: new Date().toISOString(),
      status: 'Reported',
      potholeCount: analysis.potholeCount,
      severityScore: analysis.severityScore,
      damageTypes: analysis.damageType || ['Pothole'],
      imageUrl: analysis.imageUrl || image,
      gpsCoordinates: govtTicket?.gpsCoordinates || { lat: 28.6139, lng: 77.2090 },
      citizenDossier: govtTicket?.citizenDossier,
      environmentalImpact: analysis.environmentalImpact || {
        waterLoggingRisk: analysis.severityScore >= 70 ? 'High' : 'Moderate',
        dustPollutionScore: `PM10 +${analysis.potholeCount * 20}%`,
        soilErosionHazard: analysis.potholeCount >= 2 ? 'Accelerated Runoff' : 'Contained'
      }
    };

    setTickets((prev) => [newTicket, ...prev]);
    showToast(`Govt Ticket #${regId} registered! Dispatched to ${portal.split(' ')[0]}.`);
  };

  const handleGenerateReport = async (segment: RoadSegment) => {
    setIsGeneratingReport(true);
    setMlReport('');
    const report = await generateMaintenanceReport(segment);
    setMlReport(report);
    setIsGeneratingReport(false);
  };

  const handleScheduleInspection = () => {
    if (!selectedSegment) return;
    setIsScheduling(true);
    setTimeout(() => {
      setIsScheduling(false);
      setScheduledIds((prev) => new Set(prev).add(selectedSegment.id));
      showToast(`Inspection Job #${Math.floor(1000 + Math.random() * 9000)} dispatched for ${selectedSegment.name}`);
    }, 800);
  };

  // --- Filter Bar Component ---
  const FilterBar = () => (
    <div className="flex flex-wrap items-center justify-between gap-3 bg-[#0a1f17]/80 p-4 rounded-2xl border border-emerald-900/40 shadow-xl backdrop-blur-md">
      <div className="flex items-center gap-2">
        <Filter size={16} className="text-emerald-400" />
        <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
          Filter Administrative Zone:
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {['All', ...INDIAN_ZONES].map((zone) => (
          <button
            key={zone}
            onClick={() => setSelectedDistrict(zone)}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-medium transition-all ${
              selectedDistrict === zone
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-900/50 border border-emerald-400/40'
                : 'bg-[#06140e] text-slate-400 hover:text-white hover:bg-emerald-950/60 border border-emerald-900/30'
            }`}
          >
            {zone}
          </button>
        ))}
      </div>
    </div>
  );

  // --- Render Dashboard ---
  const renderDashboard = () => (
    <div className="space-y-6 animate-in fade-in duration-500 pb-20">
      {/* Government of India Civic Redressal & Road Safety Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-rose-950/70 via-[#180a0e] to-[#0a1f17] p-6 md:p-7 border border-rose-500/30 shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div className="max-w-2xl">
          <div className="flex items-center gap-2 text-rose-400 font-mono text-xs font-bold uppercase tracking-widest mb-1.5">
            <AlertOctagon size={16} />
            Govt of India Civic Initiative • MoRTH & MoHUA
          </div>
          <h2 className="text-xl md:text-2xl font-extrabold text-white tracking-tight leading-snug">
            Citizen AI Grievance Portal: Road Potholes, Street Lights & Civic Hazards
          </h2>
          <p className="text-slate-300 text-xs md:text-sm mt-1 leading-relaxed">
            Eliminate manual complaint delays. Citizens scan road craters, dark/broken street lights, or open manholes, and AI automatically logs official tickets on <strong>CPGRAMS (pgportal.gov.in)</strong>, <strong>NHAI Rajmargyatra</strong>, and <strong>MoHUA Swachhata</strong> with verified GPS and severity evidence.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('vision')}
          className="px-5 py-3 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs md:text-sm font-mono shadow-[0_4px_16px_rgba(16,185,129,0.4)] flex items-center justify-center gap-2 border border-emerald-400/40 shrink-0 transition-all hover:scale-105"
        >
          <Zap size={16} />
          <span>Launch Civic Scanner</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#0a1f17]/80 p-5 rounded-2xl border border-rose-500/30 shadow-xl">
          <span className="text-[11px] font-mono text-rose-300 uppercase tracking-wider block mb-1">
            Critical Hotspots
          </span>
          <div className="text-3xl md:text-4xl font-black text-rose-400 font-mono">
            {filteredSegments.filter((s) => s.status === UrgencyStatus.URGENT).length}
          </div>
          <span className="text-[10px] text-slate-400 mt-2 flex items-center gap-1 font-mono">
            <Activity size={12} className="text-rose-400" /> Immediate PWD Intervention
          </span>
        </div>

        <div className="bg-[#0a1f17]/80 p-5 rounded-2xl border border-amber-500/30 shadow-xl">
          <span className="text-[11px] font-mono text-amber-300 uppercase tracking-wider block mb-1">
            Govt Tickets Registered
          </span>
          <div className="text-3xl md:text-4xl font-black text-amber-400 font-mono">
            {tickets.length}
          </div>
          <span className="text-[10px] text-slate-400 mt-2 flex items-center gap-1 font-mono">
            <FileCheck2 size={12} className="text-amber-400" /> CPGRAMS • NHAI • MoHUA
          </span>
        </div>

        <div className="bg-[#0a1f17]/80 p-5 rounded-2xl border border-emerald-500/30 shadow-xl">
          <span className="text-[11px] font-mono text-emerald-300 uppercase tracking-wider block mb-1">
            AI Vision Verifications
          </span>
          <div className="text-3xl md:text-4xl font-black text-emerald-400 font-mono">
            {segments.filter((s) => s.visualAnalysis).length}
          </div>
          <span className="text-[10px] text-slate-400 mt-2 flex items-center gap-1 font-mono">
            <Zap size={12} className="text-emerald-400" /> YOLOv8 Segmentation
          </span>
        </div>

        <div className="bg-[#0a1f17]/80 p-5 rounded-2xl border border-emerald-900/40 shadow-xl">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-1">
            Avg Surface Condition
          </span>
          <div className="text-3xl md:text-4xl font-black text-white font-mono">
            {(filteredSegments.reduce((acc, s) => acc + s.surfaceCondition, 0) / (filteredSegments.length || 1)).toFixed(1)}
            <span className="text-base text-slate-400 font-normal"> /10</span>
          </div>
          <span className="text-[10px] text-emerald-400 mt-2 flex items-center gap-1 font-mono">
            <Leaf size={12} /> Environmental Score
          </span>
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar />

      {/* Charts & Priority Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Urgency Distribution Chart */}
        <div className="lg:col-span-2 bg-[#0a1f17]/90 p-6 rounded-2xl border border-emerald-900/40 shadow-xl flex flex-col h-96 backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white text-base tracking-wide flex items-center gap-2">
              <Activity size={18} className="text-emerald-400" />
              Zone Urgency Index Breakdown
            </h3>
            <span className="text-xs font-mono text-slate-400">Scores &gt; 70 Critical</span>
          </div>

          <div className="flex-1 w-full min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={filteredSegments.slice(0, 10)} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#133827" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 10, fill: '#94a3b8' }} 
                  interval={0}
                  angle={-15}
                  textAnchor="end"
                />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={[0, 100]} />
                <Tooltip 
                  cursor={{ fill: 'rgba(16, 185, 129, 0.08)' }} 
                  contentStyle={{ 
                    backgroundColor: '#06140e', 
                    borderRadius: '12px', 
                    border: '1px solid rgba(16,185,129,0.3)', 
                    color: '#fff',
                    fontFamily: 'monospace',
                    fontSize: '12px'
                  }} 
                />
                <Bar dataKey="urgencyScore" radius={[6, 6, 0, 0]}>
                  {filteredSegments.slice(0, 10).map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.urgencyScore >= 70 ? '#f43f5e' : entry.urgencyScore >= 40 ? '#f59e0b' : '#10b981'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Priority Action List */}
        <div className="bg-[#0a1f17]/90 p-6 rounded-2xl border border-emerald-900/40 shadow-xl flex flex-col h-96 backdrop-blur-md">
          <h3 className="font-bold text-white text-base mb-3 flex items-center justify-between">
            <span>High-Hazard Roads</span>
            <span className="text-xs font-mono text-rose-400 font-bold">Action Queue</span>
          </h3>

          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
            {filteredSegments.slice(0, 6).map((s) => (
              <div 
                key={s.id} 
                onClick={() => openSegmentDetails(s)} 
                className="p-3 rounded-xl bg-[#06140e] border border-emerald-900/30 hover:border-emerald-500/40 cursor-pointer transition-all group flex items-center justify-between"
              >
                <div>
                  <h4 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
                    {s.name}
                  </h4>
                  <span className="text-[11px] font-mono text-slate-400">{s.district}</span>
                </div>
                <div className="text-right">
                  <span className={`text-base font-black font-mono ${
                    s.urgencyScore >= 70 ? 'text-rose-400' : s.urgencyScore >= 40 ? 'text-amber-400' : 'text-emerald-400'
                  }`}>
                    {s.urgencyScore.toFixed(0)}
                  </span>
                  <span className="text-[9px] uppercase tracking-wider block font-mono text-slate-400">Index</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Road Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-lg font-bold text-white">Registered Road Segments</h3>
          <span className="text-xs font-mono text-emerald-400">{filteredSegments.length} Segments Listed</span>
        </div>
        <RoadTable 
          segments={filteredSegments} 
          onSelectSegment={openSegmentDetails} 
          onDelete={handleDeleteSegment}
          scheduledIds={scheduledIds}
        />
      </div>
    </div>
  );

  return (
    <Layout 
      activeTab={activeTab} 
      setActiveTab={setActiveTab} 
      ticketCount={tickets.filter(t => t.status === 'Reported').length}
    >
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-5 left-1/2 -translate-x-1/2 z-[80] animate-in slide-in-from-top-4 duration-300 w-11/12 max-w-md">
          <div className="bg-[#0a1f17]/95 backdrop-blur-md text-white px-5 py-3.5 rounded-2xl shadow-2xl flex items-center gap-3 text-sm font-medium border border-emerald-500/50">
            <CheckCircle2 size={20} className="text-emerald-400 shrink-0" />
            <span className="leading-snug">{toastMessage}</span>
          </div>
        </div>
      )}

      {/* Selected Segment Details Modal */}
      {selectedSegment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-[#0a1f17] rounded-3xl border border-emerald-500/40 shadow-2xl w-full max-w-xl overflow-hidden animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="p-6 border-b border-emerald-900/40 flex justify-between items-start bg-[#06140e]">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/30">
                  {selectedSegment.district}
                </span>
                <h3 className="text-xl font-bold text-white mt-1.5">{selectedSegment.name}</h3>
              </div>
              <button 
                onClick={() => setSelectedSegment(null)}
                className="p-1.5 rounded-full hover:bg-emerald-900/40 text-slate-400 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-5">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-[#06140e] p-3.5 rounded-xl border border-emerald-900/40">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1">Status</span>
                  <span className={`text-base font-bold font-mono ${
                    selectedSegment.urgencyScore >= 70 ? 'text-rose-400' : 'text-emerald-400'
                  }`}>
                    {selectedSegment.status}
                  </span>
                </div>
                <div className="bg-[#06140e] p-3.5 rounded-xl border border-emerald-900/40">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1">Urgency Score</span>
                  <span className="text-base font-bold font-mono text-white">
                    {selectedSegment.urgencyScore.toFixed(0)} / 100
                  </span>
                </div>
              </div>

              {/* Visual Inspection Summary */}
              {selectedSegment.visualAnalysis && (
                <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/30 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="flex items-center gap-1 text-emerald-400 font-bold">
                      <Zap size={14} /> YOLOv8 Inspection Telemetry
                    </span>
                    <span className="text-slate-400">Verified</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs pt-1">
                    <div>
                      <span className="text-slate-400 block">Potholes Detected:</span>
                      <strong className="text-rose-400 text-sm font-mono">{selectedSegment.visualAnalysis.potholeCount}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Visual Severity:</span>
                      <strong className="text-amber-400 text-sm font-mono">{selectedSegment.visualAnalysis.severityScore}/100</strong>
                    </div>
                  </div>
                </div>
              )}

              {/* AI Report Section */}
              <div className="p-4 rounded-2xl bg-[#06140e] border border-emerald-900/40 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-mono uppercase tracking-wider text-emerald-300 font-bold flex items-center gap-1.5">
                    <Sparkles size={14} className="text-emerald-400" />
                    AI Maintenance Consultant
                  </h4>
                  {!mlReport && !isGeneratingReport && (
                    <button
                      onClick={() => handleGenerateReport(selectedSegment)}
                      className="text-xs font-mono text-emerald-300 bg-emerald-950/80 px-3 py-1 rounded-lg border border-emerald-500/30 hover:bg-emerald-900/60"
                    >
                      Generate Advice
                    </button>
                  )}
                </div>

                {isGeneratingReport ? (
                  <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 py-3">
                    <Loader2 size={16} className="animate-spin" />
                    Analyzing road deterioration and environmental factors...
                  </div>
                ) : mlReport ? (
                  <p className="text-xs text-slate-300 leading-relaxed font-sans pt-1">
                    {mlReport}
                  </p>
                ) : (
                  <p className="text-xs text-slate-400">
                    Click "Generate Advice" to receive predictive maintenance recommendations based on traffic, road age, and visual defects.
                  </p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  onClick={handleScheduleInspection}
                  disabled={isScheduling || scheduledIds.has(selectedSegment.id)}
                  className="flex-1 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs font-mono transition-all flex items-center justify-center gap-2 shadow-lg disabled:opacity-50"
                >
                  {isScheduling ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : scheduledIds.has(selectedSegment.id) ? (
                    <CheckCircle2 size={16} />
                  ) : (
                    <CalendarCheck size={16} />
                  )}
                  <span>{scheduledIds.has(selectedSegment.id) ? 'Dispatched to PWD' : 'Dispatch Repair Crew'}</span>
                </button>
                <button
                  onClick={(e) => handleDeleteSegment(selectedSegment.id, e)}
                  className="px-4 py-3 rounded-xl bg-rose-950/40 text-rose-400 hover:bg-rose-900/60 border border-rose-500/30 text-xs font-mono font-medium transition-all"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Switcher Body */}
      {activeTab === 'dashboard' && renderDashboard()}
      {activeTab === 'vision' && (
        <VisualInspection 
          onAnalysisComplete={handleVisualAnalysisComplete} 
          segments={segments} 
          syncStatus={visualSyncStatus} 
        />
      )}
      {activeTab === 'tickets' && (
        <GrievanceTickets 
          tickets={tickets} 
          onUpdateStatus={handleUpdateTicketStatus}
          onSelectTicket={(t) => {
            const seg = segments.find(s => s.id === t.segmentId);
            if (seg) openSegmentDetails(seg);
          }}
        />
      )}
      {activeTab === 'heatmap' && (
        <HeatmapGrid 
          segments={filteredSegments} 
          onSelectSegment={(id) => openSegmentDetails(id)} 
        />
      )}
      {activeTab === 'team' && <TeamModal />}
    </Layout>
  );
};

export default App;