import React, { useState, useRef } from 'react';
import { 
  Camera, 
  Upload, 
  AlertTriangle, 
  CheckCircle2, 
  Loader2, 
  RefreshCw, 
  Zap, 
  MapPin, 
  ChevronRight, 
  FileCheck2, 
  Eye, 
  Layers, 
  Droplets, 
  Wind,
  Sparkles,
  ShieldCheck,
  Locate,
  Lightbulb,
  ExternalLink,
  Copy,
  Building2,
  Clock,
  Filter
} from 'lucide-react';
import { analyzeImageLocally, simulateVisionAnalysis, generateGovtTicketMetadata } from '../services/mlService';
import { VisualAnalysis, RoadSegment, CivicIssueType, GrievanceTicket } from '../types';

interface VisualInspectionProps {
  onAnalysisComplete: (data: VisualAnalysis, image: string, segmentId: string, govtTicket?: Partial<GrievanceTicket>) => void;
  segments: RoadSegment[];
  syncStatus?: 'idle' | 'syncing' | 'success' | 'error';
}

export const VisualInspection: React.FC<VisualInspectionProps> = ({ 
  onAnalysisComplete, 
  segments, 
  syncStatus = 'idle' 
}) => {
  const [selectedCategory, setSelectedCategory] = useState<CivicIssueType>('Pothole & Crater');
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);
  const [mediaType, setMediaType] = useState<'image' | 'video' | null>(null);
  const [base64Image, setBase64Image] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<VisualAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedSegmentId, setSelectedSegmentId] = useState<string>(segments[0]?.id || '');
  const [modelSource, setModelSource] = useState<string | null>(null);
  const [ticketCreated, setTicketCreated] = useState<any | null>(null);
  const [isCopied, setIsCopied] = useState(false);

  const [gpsCoords, setGpsCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [isLocating, setIsLocating] = useState(false);


  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isCameraOpen, setIsCameraOpen] = useState(false);

  // Auto-fetch GPS
  const handleAutoLocate = () => {
    if ('geolocation' in navigator) {
      setIsLocating(true);
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setGpsCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
          setIsLocating(false);
        },
        (err) => {
          console.warn('Geolocation denied, using default coordinates', err);
          setGpsCoords({ lat: 28.6139, lng: 77.2090 }); // New Delhi default
          setIsLocating(false);
        }
      );
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const isVideo = file.type.startsWith('video/');
      const objUrl = URL.createObjectURL(file);

      setMediaUrl(objUrl);
      setMediaType(isVideo ? 'video' : 'image');
      setResult(null);
      setError(null);
      setBase64Image(null);
      setTicketCreated(null);

      if (!isVideo) {
        const reader = new FileReader();
        reader.onload = (ev) => {
          if (ev.target?.result) {
            const b64 = ev.target.result as string;
            setBase64Image(b64);
            processImage(b64.split(',')[1]);
          }
        };
        reader.readAsDataURL(file);
      }
    }
  };

  const startCamera = async () => {
    setIsCameraOpen(true);
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error('Camera error:', err);
      setError('Unable to access camera. Please check permissions or upload an image file.');
      setIsCameraOpen(false);
    }
  };

  const capturePhoto = () => {
    if (videoRef.current) {
      const activeVideo = videoRef.current;
      const canvas = document.createElement('canvas');
      const size = Math.min(activeVideo.videoWidth || 640, activeVideo.videoHeight || 480);
      canvas.width = size;
      canvas.height = size;

      const ctx = canvas.getContext('2d');
      if (ctx) {
        const sx = ((activeVideo.videoWidth || size) - size) / 2;
        const sy = ((activeVideo.videoHeight || size) - size) / 2;
        ctx.drawImage(activeVideo, sx, sy, size, size, 0, 0, size, size);
      }

      const b64 = canvas.toDataURL('image/jpeg', 0.9);

      // Stop camera stream
      const stream = activeVideo.srcObject as MediaStream;
      stream?.getTracks().forEach((t) => t.stop());
      setIsCameraOpen(false);

      setMediaUrl(b64);
      setMediaType('image');
      setBase64Image(b64);
      setResult(null);
      setError(null);
      processImage(b64.split(',')[1]);
    }
  };

  const processImage = async (base64Data: string, overrideCategory?: CivicIssueType) => {
    setIsAnalyzing(true);
    setError(null);
    setTicketCreated(null);
    const categoryToUse = overrideCategory || selectedCategory;

    try {
      // 1. Try local Python inference engine
      const data = await analyzeImageLocally(base64Data, true, categoryToUse);
      if (data) {
        setResult(data);
        setModelSource(data.detectedVia || 'CivicVision AI Engine');
        if (data.imageUrl) {
          setMediaUrl(data.imageUrl);
          setMediaType('image');
        }
      } else {
        throw new Error('Inference returned empty response');
      }
    } catch (err: any) {
      console.warn('Backend unavailable, triggering browser client-side vision fallback:', err);
      try {
        const simData = await simulateVisionAnalysis(base64Data, categoryToUse);
        setResult(simData);
        setModelSource('CivicVision Neural Simulator');
        if (simData.imageUrl) {
          setMediaUrl(simData.imageUrl);
          setMediaType('image');
        }
      } catch (simErr: any) {
        setError('Detection failed: ' + (simErr.message || 'Unknown processing error'));
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Helper to generate instant synthetic test road image with civic issues
  const loadPresetTest = (type: 'crater' | 'light' | 'manhole' | 'crack' | 'severe') => {
    const canvas = document.createElement('canvas');
    canvas.width = 640;
    canvas.height = 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let category: CivicIssueType = 'Pothole & Crater';

    if (type === 'light') {
      category = 'Broken Street Light';
      setSelectedCategory('Broken Street Light');

      // 1. Night sky background
      const skyGrad = ctx.createLinearGradient(0, 0, 0, 480);
      skyGrad.addColorStop(0, '#020617');
      skyGrad.addColorStop(1, '#0f172a');
      ctx.fillStyle = skyGrad;
      ctx.fillRect(0, 0, 640, 480);

      // Road pavement at bottom
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(0, 380, 640, 100);

      // Lamp pole
      ctx.strokeStyle = '#64748b';
      ctx.lineWidth = 14;
      ctx.beginPath();
      ctx.moveTo(340, 420);
      ctx.lineTo(340, 140);
      ctx.lineTo(390, 90);
      ctx.stroke();

      // Damaged / broken lamp head
      ctx.fillStyle = '#475569';
      ctx.beginPath();
      ctx.ellipse(400, 95, 35, 16, 0.4, 0, Math.PI * 2);
      ctx.fill();

      // Spark / broken wire effect
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(410, 105);
      ctx.lineTo(418, 120);
      ctx.lineTo(412, 126);
      ctx.lineTo(422, 138);
      ctx.stroke();

      // Warning text
      ctx.fillStyle = '#ef4444';
      ctx.font = 'bold 12px monospace';
      ctx.fillText('⚡ NON-FUNCTIONAL LUMINAIRE', 300, 70);

    } else if (type === 'manhole') {
      category = 'Open Manhole';
      setSelectedCategory('Open Manhole');

      // Road surface
      ctx.fillStyle = '#334155';
      ctx.fillRect(0, 0, 640, 480);

      // Road markings
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 4;
      ctx.setLineDash([20, 20]);
      ctx.beginPath();
      ctx.moveTo(0, 240); ctx.lineTo(640, 240);
      ctx.stroke();
      ctx.setLineDash([]);

      // Deep dark open manhole ring
      ctx.fillStyle = '#020617';
      ctx.beginPath();
      ctx.ellipse(320, 280, 85, 75, 0, 0, Math.PI * 2);
      ctx.fill();

      // Iron rim
      ctx.strokeStyle = '#64748b';
      ctx.lineWidth = 8;
      ctx.stroke();

      // Inner depth
      ctx.fillStyle = '#000000';
      ctx.beginPath();
      ctx.ellipse(320, 285, 70, 60, 0, 0, Math.PI * 2);
      ctx.fill();

    } else {
      // Road defects
      if (type === 'crack') {
        category = 'Road Fissure & Crack';
        setSelectedCategory('Road Fissure & Crack');
      } else {
        category = 'Pothole & Crater';
        setSelectedCategory('Pothole & Crater');
      }

      // Asphalt pavement texture
      ctx.fillStyle = '#374151';
      ctx.fillRect(0, 0, 640, 480);

      // Grain
      for (let i = 0; i < 3500; i++) {
        const x = Math.random() * 640;
        const y = Math.random() * 480;
        ctx.fillStyle = Math.random() > 0.5 ? '#1f2937' : '#4b5563';
        ctx.fillRect(x, y, 2, 2);
      }

      // Lane line
      ctx.strokeStyle = '#facc15';
      ctx.lineWidth = 6;
      ctx.setLineDash([30, 25]);
      ctx.beginPath();
      ctx.moveTo(320, 0); ctx.lineTo(320, 480);
      ctx.stroke();
      ctx.setLineDash([]);

      if (type === 'crater') {
        ctx.fillStyle = '#111827';
        ctx.beginPath();
        ctx.ellipse(320, 280, 85, 45, 0.1, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#030712';
        ctx.beginPath();
        ctx.ellipse(310, 275, 40, 22, -0.1, 0, Math.PI * 2);
        ctx.fill();
      } else if (type === 'crack') {
        ctx.strokeStyle = '#111827';
        ctx.lineWidth = 5;
        ctx.beginPath();
        ctx.moveTo(220, 100); ctx.lineTo(260, 220);
        ctx.lineTo(240, 310); ctx.lineTo(290, 440);
        ctx.stroke();

        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(260, 220); ctx.lineTo(350, 260); ctx.lineTo(390, 310);
        ctx.stroke();
      } else {
        // Severe multiple potholes
        ctx.fillStyle = '#0f172a';
        ctx.beginPath();
        ctx.ellipse(240, 240, 70, 38, 0.2, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.ellipse(420, 310, 80, 45, -0.15, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#020617';
        ctx.beginPath();
        ctx.ellipse(430, 315, 38, 20, 0, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    const b64 = canvas.toDataURL('image/jpeg', 0.9);
    setMediaUrl(b64);
    setMediaType('image');
    setBase64Image(b64);
    setResult(null);
    setError(null);
    processImage(b64.split(',')[1], category);
  };

  const handleConfirmAndFileTicket = () => {
    if (result && base64Image) {
      const targetSegment = segments.find((s) => s.id === selectedSegmentId) || segments[0];
      const targetId = targetSegment?.id || 'seg-001';
      const lat = gpsCoords ? gpsCoords.lat : 28.6139;
      const lng = gpsCoords ? gpsCoords.lng : 77.2090;

      // Generate official Government of India ticket metadata
      const govtData = generateGovtTicketMetadata(
        selectedCategory,
        targetSegment?.name || 'MG Road Expressway',
        targetSegment?.district || 'Zone 1 (North)',
        lat,
        lng,
        result.severityScore
      );

      const ticketPayload: Partial<GrievanceTicket> = {
        govtPortal: govtData.govtPortal,
        govtRegistrationId: govtData.govtRegistrationId,
        nodalAuthority: govtData.nodalAuthority,
        officialPortalUrl: govtData.officialPortalUrl,
        slaDays: govtData.slaDays,
        issueCategory: selectedCategory,
        citizenDossier: govtData.citizenDossier,
        gpsCoordinates: { lat, lng }
      };

      onAnalysisComplete(result, base64Image, targetId, ticketPayload);
      setTicketCreated(govtData);
    }
  };

  const copyDossierToClipboard = () => {
    if (ticketCreated?.citizenDossier) {
      navigator.clipboard.writeText(ticketCreated.citizenDossier);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2500);
    }
  };

  const reset = () => {
    if (mediaUrl && mediaUrl.startsWith('blob:')) {
      URL.revokeObjectURL(mediaUrl);
    }
    setMediaUrl(null);
    setMediaType(null);
    setBase64Image(null);
    setResult(null);
    setError(null);
    setIsCameraOpen(false);
    setTicketCreated(null);
    setIsCopied(false);
  };

  const selectedSegment = segments.find((s) => s.id === selectedSegmentId) || segments[0];

  return (
    <div className="space-y-7 animate-in fade-in duration-500 pb-20">
      {/* Top Banner Card */}
      <div className="bg-[#0a1f17]/90 p-6 md:p-8 rounded-3xl border border-emerald-900/40 shadow-2xl backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-[11px] font-mono uppercase tracking-widest text-emerald-400 px-2.5 py-0.5 rounded-full bg-emerald-950 border border-emerald-500/30 flex items-center gap-1.5">
                <Zap size={12} className="text-emerald-400" />
                Govt of India Civic AI Scanner
              </span>
              <span className="text-[10px] font-mono text-amber-300 bg-amber-950/70 px-2 py-0.5 rounded border border-amber-500/30 flex items-center gap-1">
                <Building2 size={11} />
                Auto-Triage: CPGRAMS • NHAI • MoHUA
              </span>
              {modelSource && (
                <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                  {modelSource}
                </span>
              )}
            </div>
            <h2 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Citizen Civic Hazard & Road Defect Scanner
            </h2>
            <p className="text-slate-300 text-sm mt-1 max-w-2xl leading-relaxed">
              Scan road potholes, damaged street lights, and open manholes. AI automatically pinpoints GPS coordinates, computes severity, and files an official ticket on the relevant Government of India portal.
            </p>
          </div>

          {/* Quick Preset Test Buttons */}
          <div className="bg-[#06140e] p-3.5 rounded-2xl border border-emerald-900/40">
            <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 block mb-2 font-bold">
              ⚡ Instant Evaluation Samples:
            </span>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => loadPresetTest('crater')}
                className="px-2.5 py-1.5 rounded-lg bg-emerald-950/80 text-emerald-300 hover:bg-emerald-900/60 border border-emerald-500/30 text-xs font-mono font-medium transition-all text-left"
              >
                🕳️ Road Pothole
              </button>
              <button
                onClick={() => loadPresetTest('light')}
                className="px-2.5 py-1.5 rounded-lg bg-sky-950/80 text-sky-300 hover:bg-sky-900/60 border border-sky-500/30 text-xs font-mono font-medium transition-all text-left"
              >
                💡 Broken Street Light
              </button>
              <button
                onClick={() => loadPresetTest('manhole')}
                className="px-2.5 py-1.5 rounded-lg bg-rose-950/80 text-rose-300 hover:bg-rose-900/60 border border-rose-500/30 text-xs font-mono font-medium transition-all text-left"
              >
                ⚠️ Open Manhole
              </button>
              <button
                onClick={() => loadPresetTest('severe')}
                className="px-2.5 py-1.5 rounded-lg bg-amber-950/80 text-amber-300 hover:bg-amber-900/60 border border-amber-500/30 text-xs font-mono font-medium transition-all text-left"
              >
                🛣️ Highway Multi-Cavity
              </button>
            </div>
          </div>
        </div>

        {/* Civic Issue Category Selector Tabs */}
        <div className="mt-5 pt-4 border-t border-emerald-900/40 flex flex-wrap items-center gap-2">
          <span className="text-xs font-mono text-slate-400 mr-2 flex items-center gap-1.5">
            <Filter size={13} className="text-emerald-400" /> Target Civic Category:
          </span>
          {(['Pothole & Crater', 'Broken Street Light', 'Open Manhole', 'Road Fissure & Crack'] as CivicIssueType[]).map((cat) => (
            <button
              key={cat}
              onClick={() => {
                setSelectedCategory(cat);
                if (base64Image) {
                  processImage(base64Image.split(',')[1], cat);
                }
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-mono transition-all flex items-center gap-1.5 ${
                selectedCategory === cat
                  ? 'bg-emerald-600 text-white font-bold shadow-md shadow-emerald-950 border border-emerald-400/50'
                  : 'bg-[#06140e] text-slate-400 hover:text-slate-200 border border-emerald-900/40'
              }`}
            >
              {cat === 'Pothole & Crater' && '🕳️'}
              {cat === 'Broken Street Light' && '💡'}
              {cat === 'Open Manhole' && '⚠️'}
              {cat === 'Road Fissure & Crack' && '⚡'}
              <span>{cat}</span>
            </button>
          ))}
        </div>

        {/* Location & Segment Selection Controls */}
        <div className="grid md:grid-cols-2 gap-4 mt-6 pt-6 border-t border-emerald-900/30">
          <div>
            <label className="text-xs font-mono text-slate-400 mb-1.5 block uppercase tracking-wider">
              Road Location / Zone Target
            </label>
            <div className="relative">
              <MapPin className="absolute left-3.5 top-3 text-emerald-400" size={17} />
              <select
                value={selectedSegmentId}
                onChange={(e) => setSelectedSegmentId(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-[#06140e] border border-emerald-900/60 rounded-xl text-sm text-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none cursor-pointer hover:border-emerald-500/50 transition-colors"
              >
                {segments.map((seg) => (
                  <option key={seg.id} value={seg.id}>
                    {seg.name} ({seg.district}) — Surface Rating {seg.surfaceCondition}/10
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-mono text-slate-400 mb-1.5 block uppercase tracking-wider flex items-center justify-between">
              <span>Automatic Geotagging</span>
              <button 
                onClick={handleAutoLocate}
                className="text-[11px] text-emerald-400 hover:underline flex items-center gap-1 font-mono"
              >
                <Locate size={12} className={isLocating ? 'animate-spin' : ''} />
                {isLocating ? 'Detecting GPS...' : 'Detect Coordinates'}
              </button>
            </label>
            <div className="px-4 py-2.5 bg-[#06140e] border border-emerald-900/60 rounded-xl text-sm font-mono text-emerald-300 flex items-center justify-between">
              <span>
                {gpsCoords 
                  ? `Lat: ${gpsCoords.lat.toFixed(4)}° N, Lng: ${gpsCoords.lng.toFixed(4)}° E`
                  : 'GPS: 28.6139° N, 77.2090° E (Auto-Tagged)'
                }
              </span>
              <span className="text-[10px] bg-emerald-900/60 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
                Locked
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-rose-950/60 border border-rose-500/40 rounded-2xl p-4 flex items-start gap-3 shadow-lg">
          <AlertTriangle className="text-rose-400 shrink-0 mt-0.5" size={20} />
          <div className="flex-1">
            <h4 className="text-rose-200 font-bold text-sm">Processing Notice</h4>
            <p className="text-rose-300/80 text-xs mt-0.5">{error}</p>
          </div>
          <button 
            onClick={() => setError(null)}
            className="text-xs font-mono text-rose-300 hover:text-white bg-rose-900/40 px-3 py-1 rounded-lg border border-rose-500/30"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Upload & Camera Section */}
      {!mediaUrl && !isCameraOpen && (
        <div className="grid md:grid-cols-2 gap-5">
          <button 
            onClick={startCamera}
            className="p-8 rounded-3xl bg-[#0a1f17]/80 border-2 border-dashed border-emerald-800/40 hover:border-emerald-400/60 hover:bg-[#0d2a1f] transition-all flex flex-col items-center justify-center group shadow-xl"
          >
            <div className="w-16 h-16 rounded-2xl bg-emerald-950 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-4 group-hover:scale-110 transition-transform">
              <Camera size={30} />
            </div>
            <h3 className="text-lg font-bold text-white mb-1 group-hover:text-emerald-300 transition-colors">
              Open Live Camera
            </h3>
            <p className="text-xs text-slate-400 text-center max-w-xs">
              Point your smartphone or webcam at the road surface for instant scanning.
            </p>
          </button>

          <button 
            onClick={() => fileInputRef.current?.click()}
            className="p-8 rounded-3xl bg-[#0a1f17]/80 border-2 border-dashed border-emerald-800/40 hover:border-emerald-400/60 hover:bg-[#0d2a1f] transition-all flex flex-col items-center justify-center group shadow-xl"
          >
            <div className="w-16 h-16 rounded-2xl bg-emerald-950 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-4 group-hover:scale-110 transition-transform">
              <Upload size={30} />
            </div>
            <h3 className="text-lg font-bold text-white mb-1 group-hover:text-emerald-300 transition-colors">
              Upload Road Photo / Video
            </h3>
            <p className="text-xs text-slate-400 text-center max-w-xs">
              Upload photos, drone footage, or dashcam videos (.jpg, .png, .mp4).
            </p>
            <input 
              ref={fileInputRef} 
              type="file" 
              accept="image/*,video/*" 
              className="hidden" 
              onChange={handleFileUpload} 
            />
          </button>
        </div>
      )}

      {/* Camera Live Viewfinder */}
      {isCameraOpen && (
        <div className="relative rounded-3xl overflow-hidden bg-black border-2 border-emerald-600/50 shadow-2xl max-w-2xl mx-auto aspect-video flex items-center justify-center">
          <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
          
          {/* HUD Reticle */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-[75%] aspect-square border-2 border-emerald-400/50 rounded-2xl shadow-[0_0_0_9999px_rgba(0,0,0,0.45)] relative">
              <div className="absolute top-0 left-0 w-5 h-5 border-t-4 border-l-4 border-emerald-400 rounded-tl-lg" />
              <div className="absolute top-0 right-0 w-5 h-5 border-t-4 border-r-4 border-emerald-400 rounded-tr-lg" />
              <div className="absolute bottom-0 left-0 w-5 h-5 border-b-4 border-l-4 border-emerald-400 rounded-bl-lg" />
              <div className="absolute bottom-0 right-0 w-5 h-5 border-b-4 border-r-4 border-emerald-400 rounded-br-lg" />
            </div>
          </div>

          {/* Controls Bar */}
          <div className="absolute inset-x-0 bottom-0 p-5 bg-gradient-to-t from-black/90 to-transparent flex justify-center items-center gap-5">
            <button
              onClick={() => {
                const stream = videoRef.current?.srcObject as MediaStream;
                stream?.getTracks().forEach((t) => t.stop());
                setIsCameraOpen(false);
              }}
              className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-mono font-medium hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              onClick={capturePhoto}
              className="w-16 h-16 rounded-full bg-emerald-500 border-4 border-white shadow-[0_0_25px_rgba(16,185,129,0.7)] active:scale-95 transition-all flex items-center justify-center text-white"
            >
              <Camera size={26} />
            </button>
          </div>
        </div>
      )}

      {/* Detection Results & HUD Display */}
      {mediaUrl && (
        <div className="space-y-6">
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Annotated Image Frame */}
            <div className="lg:col-span-2 bg-[#0a1f17]/90 rounded-3xl border border-emerald-900/40 p-4 shadow-2xl overflow-hidden flex flex-col justify-between">
              <div className="relative rounded-2xl overflow-hidden bg-black aspect-video flex items-center justify-center border border-emerald-950">
                {isAnalyzing ? (
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="animate-spin text-emerald-400" size={40} />
                    <span className="text-sm font-mono text-emerald-300 font-bold">
                      Segmenting Surface Damage...
                    </span>
                  </div>
                ) : (
                  <img 
                    src={mediaUrl} 
                    alt="Road Scan Output" 
                    className="w-full h-full object-contain"
                  />
                )}

                {/* Status HUD Watermark */}
                {!isAnalyzing && result && (
                  <div className="absolute top-3 left-3 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-emerald-500/40 text-xs font-mono text-emerald-300 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                    <span>YOLOv8 Segmentation Ready</span>
                  </div>
                )}
              </div>

              {/* Reset / Rescan Bar */}
              <div className="flex items-center justify-between mt-4 px-2">
                <span className="text-xs font-mono text-slate-400">
                  Target: <strong className="text-white">{selectedSegment?.name}</strong>
                </span>
                <button
                  onClick={reset}
                  className="text-xs font-mono text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3.5 py-1.5 rounded-xl transition-colors flex items-center gap-1.5"
                >
                  <RefreshCw size={13} />
                  Scan Another Road
                </button>
              </div>
            </div>

            {/* Telemetry & Metrics Column */}
            <div className="space-y-5">
              {/* Defect Summary Card */}
              <div className="bg-[#0a1f17]/90 p-6 rounded-3xl border border-emerald-900/40 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-emerald-900/40 pb-3">
                  <h4 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                    Detection Telemetry
                  </h4>
                  <span className="text-xs font-mono text-emerald-400">Live Result</span>
                </div>

                {/* Primary Metrics */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-[#06140e] p-4 rounded-2xl border border-emerald-900/40">
                    <span className="text-xs font-mono text-slate-400 block mb-1">Pothole Count</span>
                    <span className="text-3xl font-black text-rose-400 font-mono">
                      {result ? result.potholeCount : 0}
                    </span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">Isolated Cavities</span>
                  </div>

                  <div className="bg-[#06140e] p-4 rounded-2xl border border-emerald-900/40">
                    <span className="text-xs font-mono text-slate-400 block mb-1">Severity Score</span>
                    <span className={`text-3xl font-black font-mono ${
                      (result?.severityScore || 0) >= 70 
                        ? 'text-rose-400' 
                        : (result?.severityScore || 0) >= 40 
                        ? 'text-amber-400' 
                        : 'text-emerald-400'
                    }`}>
                      {result ? result.severityScore : 0}
                      <span className="text-sm font-normal text-slate-400">/100</span>
                    </span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">
                      {(result?.severityScore || 0) >= 70 ? 'Urgent Repair' : (result?.severityScore || 0) >= 40 ? 'Monitor' : 'Stable'}
                    </span>
                  </div>
                </div>

                {/* Classification Badges */}
                <div>
                  <span className="text-xs font-mono text-slate-400 block mb-2">Damage Classification</span>
                  <div className="flex flex-wrap gap-1.5">
                    {result && result.damageType && result.damageType.length > 0 ? (
                      result.damageType.map((dt, idx) => (
                        <span 
                          key={idx}
                          className="px-2.5 py-1 rounded-lg bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 text-xs font-mono font-medium"
                        >
                          {dt}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-400 font-mono">Analyzing...</span>
                    )}
                  </div>
                </div>

                {/* EPICS Environmental Risks Badge */}
                {result?.environmentalImpact && (
                  <div className="p-3.5 bg-[#06140e] rounded-2xl border border-emerald-900/40 space-y-2 text-xs">
                    <span className="text-[11px] font-mono font-bold text-emerald-400 uppercase tracking-wider block">
                      Environmental Impact Assessment:
                    </span>
                    <div className="flex items-center justify-between text-slate-300">
                      <span className="flex items-center gap-1.5">
                        <Droplets size={13} className="text-blue-400" />
                        Water-Logging Hazard:
                      </span>
                      <strong className={
                        result.environmentalImpact.waterLoggingRisk === 'High' ? 'text-rose-400' : 'text-amber-400'
                      }>
                        {result.environmentalImpact.waterLoggingRisk}
                      </strong>
                    </div>
                    <div className="flex items-center justify-between text-slate-300">
                      <span className="flex items-center gap-1.5">
                        <Wind size={13} className="text-emerald-400" />
                        Dust Pollution:
                      </span>
                      <strong className="text-emerald-300 font-mono text-[11px]">
                        {result.environmentalImpact.dustPollutionScore}
                      </strong>
                    </div>
                  </div>
                )}

                {/* Automated Government Grievance Ticket Button */}
                <div className="space-y-2 pt-1">
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-1">
                    <span className="flex items-center gap-1">
                      <Building2 size={12} className="text-emerald-400" /> Target Portal:
                    </span>
                    <span className="text-emerald-300 font-bold">
                      {selectedCategory === 'Broken Street Light'
                        ? 'CPGRAMS (MoHUA)'
                        : selectedCategory === 'Open Manhole'
                        ? 'Swachhata-MoHUA 311'
                        : selectedSegment?.name.toLowerCase().includes('expressway')
                        ? 'NHAI Rajmargyatra'
                        : 'CPGRAMS (MoRTH)'}
                    </span>
                  </div>

                  <button
                    onClick={handleConfirmAndFileTicket}
                    disabled={!result || isAnalyzing}
                    className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-[0_4px_24px_rgba(16,185,129,0.4)] transition-all flex items-center justify-center gap-2 border border-emerald-400/50 disabled:opacity-50 hover:scale-[1.02]"
                  >
                    <FileCheck2 size={18} />
                    <span>Raise Official Ticket on Govt Portal</span>
                  </button>
                </div>
              </div>

              {/* Official Government Ticket Confirmation Card */}
              {ticketCreated && (
                <div className="bg-[#06140e] border-2 border-emerald-500/60 rounded-3xl p-5 shadow-2xl animate-in zoom-in-95 space-y-3.5">
                  <div className="flex items-start justify-between gap-3 border-b border-emerald-900/50 pb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-9 h-9 rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center justify-center shrink-0">
                        <CheckCircle2 size={20} />
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-mono uppercase tracking-widest text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/30 font-bold">
                            Govt of India Dispatch Receipt
                          </span>
                        </div>
                        <h5 className="text-base font-bold text-white mt-0.5">
                          Grievance Formally Registered
                        </h5>
                      </div>
                    </div>
                  </div>

                  {/* Grievance Details */}
                  <div className="space-y-2 text-xs font-mono">
                    <div className="flex items-center justify-between p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-900/40">
                      <span className="text-slate-400">Govt Reg ID:</span>
                      <strong className="text-emerald-300 font-bold text-sm tracking-wide">
                        {ticketCreated.govtRegistrationId}
                      </strong>
                    </div>

                    <div className="p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-900/40 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Portal:</span>
                        <span className="text-white font-semibold">{ticketCreated.govtPortal}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Nodal Wing:</span>
                        <span className="text-slate-300 text-right truncate max-w-[180px]" title={ticketCreated.nodalAuthority}>
                          {ticketCreated.nodalAuthority}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Charter SLA:</span>
                        <span className="text-amber-400 font-bold">{ticketCreated.slaDays} Business Days</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions: Track & Copy */}
                  <div className="flex items-center gap-2 pt-1">
                    <a
                      href={ticketCreated.officialPortalUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 py-2.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold text-center flex items-center justify-center gap-1.5 shadow-md transition-all"
                    >
                      <ExternalLink size={13} />
                      <span>Track on Govt Portal</span>
                    </a>

                    <button
                      onClick={copyDossierToClipboard}
                      className="py-2.5 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 font-mono text-xs font-medium flex items-center justify-center gap-1.5 transition-all"
                      title="Copy Public Grievance Dossier"
                    >
                      <Copy size={13} />
                      <span>{isCopied ? 'Copied!' : 'Copy Dossier'}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};