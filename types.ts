export enum TrafficLoad {
  LOW = 'Low',
  MEDIUM = 'Medium',
  HIGH = 'High',
  EXTREME = 'Extreme'
}

export enum WeatherImpact {
  MILD = 'Mild',
  MODERATE = 'Moderate',
  SEVERE = 'Severe' // e.g., freeze-thaw cycles, heavy flooding
}

export enum UrgencyStatus {
  STABLE = 'Stable',
  MONITOR = 'Monitor',
  URGENT = 'Urgent Repair'
}

export interface EnvironmentalImpact {
  waterLoggingRisk: 'High' | 'Moderate' | 'Low';
  dustPollutionScore: string;
  soilErosionHazard: string;
}

export type CivicIssueType = 
  | 'Pothole & Crater' 
  | 'Broken Street Light' 
  | 'Open Manhole' 
  | 'Road Fissure & Crack' 
  | 'Water-Logging Hazard';

export type GovtPortal = 
  | 'CPGRAMS (MoRTH - Ministry of Road Transport)' 
  | 'CPGRAMS (MoHUA - Urban Affairs)' 
  | 'NHAI Rajmargyatra (National Highways)' 
  | 'Swachhata-MoHUA (Urban Local Body 311)';

export interface VisualAnalysis {
  potholeCount: number;
  severityScore: number; // 0-100
  damageType: string[]; // e.g. ["Pothole", "Broken Street Light", "Open Manhole"]
  issueCategory?: CivicIssueType;
  imageUrl?: string;
  processedAt: string;
  isAIFallback?: boolean;
  environmentalImpact?: EnvironmentalImpact;
  detectedVia?: string;
}

export enum MaintenanceStatus {
  IDLE = "Idle",
  REPORTED = "Reported",
  ANALYZING = "In Review",
  PLANNED = "Scheduled",
  FIXED = "Repaired"
}

export interface GrievanceTicket {
  ticketId: string; // e.g. "RS-2026-8492"
  govtRegistrationId: string; // e.g. "MORTE/E/2026/0048192" or "NHAI-RJY-2026-9281"
  govtPortal: GovtPortal;
  nodalAuthority: string; // e.g. "NHAI Project Director, Delhi-NCR" or "Municipal Corporation PWD Division"
  officialPortalUrl: string; // https://pgportal.gov.in or https://nhai.gov.in
  slaDays: number; // SLA turnaround under Citizen Charter (e.g. 7 days)
  issueCategory: CivicIssueType;
  segmentId: string;
  roadName: string;
  district: string;
  createdAt: string;
  status: 'Reported' | 'In Review' | 'Scheduled' | 'Repaired';
  potholeCount: number;
  severityScore: number;
  damageTypes: string[];
  gpsCoordinates?: { lat: number; lng: number };
  imageUrl?: string;
  environmentalImpact?: EnvironmentalImpact;
  citizenDossier?: string;
}

export interface RoadSegment {
  id: string;
  name: string;
  district: string;
  trafficLoad: TrafficLoad;
  ageYears: number; // Years since last resurfacing
  weatherImpact: WeatherImpact;
  surfaceCondition: number; // 1-10 scale (10 is perfect)
  // Calculated fields
  urgencyScore: number; // 0-100
  status: UrgencyStatus;
  visualAnalysis?: VisualAnalysis;
  maintenanceStatus?: MaintenanceStatus;
  progress?: number; // 0-100
  coordinates?: { lat: number; lng: number };
  ticketId?: string;
}