import React from 'react';
import { 
  Users, 
  GraduationCap, 
  Leaf, 
  AlertOctagon, 
  Droplets, 
  Wind, 
  Layers, 
  Sparkles,
  ShieldCheck,
  Cpu
} from 'lucide-react';

export const TeamModal: React.FC = () => {
  const teamMembers = [
    { name: 'Kevin George', initials: 'KG', role: 'System Architecture & Integration' },
    { name: 'Hitesh Chaudhary', initials: 'HC', role: 'Machine Learning & Computer Vision' },
    { name: 'Parth Jangir', initials: 'PJ', role: 'Full-Stack Engine & Backend APIs' },
    { name: 'Shrisai Kolkondi', initials: 'SK', role: 'Data Pipelines & Annotation' },
    { name: 'Ishika Mittal', initials: 'IM', role: 'Civil Metrics & Severity Scoring' },
    { name: 'Darsana Shaji', initials: 'DS', role: 'UI/UX & Environmental Analysis' },
  ];

  const environmentalPillars = [
    {
      icon: Droplets,
      title: 'Water-Logging & Breeding',
      description: 'Unrepaired potholes trap stagnant water, accelerating mosquito breeding and waterborne disease risk across urban zones.'
    },
    {
      icon: Layers,
      title: 'Soil Erosion & Runoff',
      description: 'Broken asphalt surfaces speed up sub-base erosion and uncontrolled sediment runoff into municipal storm drains.'
    },
    {
      icon: Wind,
      title: 'Air & Dust Pollution',
      description: 'Crumbling road edges and tire pulverization raise particulate matter (PM2.5 / PM10), deteriorating local breathable air quality.'
    },
    {
      icon: Leaf,
      title: 'Resource-Efficient Maintenance',
      description: 'Early, AI-driven detection cuts material waste and repeat cold-mix patching, ensuring sustainable infrastructure life.'
    }
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-20">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#0F382A] via-[#0b281e] to-[#04130e] border border-emerald-500/30 p-8 md:p-10 shadow-2xl">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/80 border border-emerald-400/40 text-emerald-300 text-xs font-mono uppercase tracking-widest mb-4">
            <Leaf size={14} className="text-emerald-400" />
            EPICS • Environmental Monitoring
          </div>
          <h1 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight mb-3">
            RoadSense <span className="text-emerald-400">AI</span>
          </h1>
          <p className="text-emerald-100/90 text-base md:text-lg leading-relaxed font-normal">
            AI-Powered Road & Civil Structure Damage Detection with Automated Municipal Grievance Reporting.
          </p>

          {/* Supervisor Card */}
          <div className="mt-6 pt-6 border-t border-emerald-800/40 flex flex-wrap items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-900/60 border border-emerald-400/30 flex items-center justify-center text-emerald-300 shadow-inner">
              <GraduationCap size={24} />
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-emerald-300/80 font-mono">Under the Guidance of Supervisor</p>
              <h4 className="text-lg font-bold text-white">Dr. M. Suresh</h4>
              <p className="text-xs text-slate-300">Faculty Mentor, EPICS Program</p>
            </div>
          </div>
        </div>

        {/* Ambient Decorative Glow */}
        <div className="absolute right-0 top-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* Critical Indian Road Stats (Slide 2) */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-[#0a1f17]/90 rounded-2xl border border-rose-500/30 p-7 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <AlertOctagon size={24} className="text-rose-400" />
            <span className="text-xs font-mono uppercase tracking-widest text-rose-300">MoRTH Official Data</span>
          </div>
          <div className="text-4xl md:text-5xl font-black text-rose-400 font-mono tracking-tight mt-3">
            9,438
          </div>
          <p className="text-slate-300 text-sm font-medium mt-2 leading-relaxed">
            Lives lost to pothole-related road crashes in India between 2020–2024 — a 53% rise in five years.
          </p>
        </div>

        <div className="bg-[#0a1f17]/90 rounded-2xl border border-amber-500/30 p-7 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <AlertOctagon size={24} className="text-amber-400" />
            <span className="text-xs font-mono uppercase tracking-widest text-amber-300">Daily Human Toll</span>
          </div>
          <div className="text-4xl md:text-5xl font-black text-amber-400 font-mono tracking-tight mt-3">
            80+
          </div>
          <p className="text-slate-300 text-sm font-medium mt-2 leading-relaxed">
            People die on average, every single day in India due to poor and deteriorating road conditions.
          </p>
        </div>
      </div>

      {/* The 4 Environmental Monitoring Pillars (Slide 3) */}
      <div>
        <div className="mb-4">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <Leaf size={20} className="text-emerald-400" />
            Environmental Monitoring Domain
          </h3>
          <p className="text-slate-400 text-xs mt-1">
            Why civil structure defect detection directly addresses critical environmental hazards.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
          {environmentalPillars.map((p, idx) => (
            <div 
              key={idx}
              className="bg-[#0a1f17]/80 rounded-2xl border border-emerald-900/40 p-5 shadow-lg hover:border-emerald-500/40 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="w-10 h-10 rounded-xl bg-emerald-950 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-3.5">
                  <p.icon size={20} />
                </div>
                <h4 className="text-base font-bold text-white mb-2">{p.title}</h4>
                <p className="text-xs text-slate-300 leading-relaxed">{p.description}</p>
              </div>
              <div className="mt-4 pt-3 border-t border-emerald-900/30 text-[10px] font-mono text-emerald-400 uppercase tracking-wider">
                Pillar #{idx + 1}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Team Members Grid (Slide 14) */}
      <div>
        <div className="mb-4">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <Users size={20} className="text-emerald-400" />
            Project Team Members
          </h3>
          <p className="text-slate-400 text-xs mt-1">
            EPICS Project Team behind RoadSense AI.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-5">
          {teamMembers.map((member, idx) => (
            <div 
              key={idx}
              className="bg-[#0a1f17]/80 rounded-2xl border border-emerald-900/40 p-5 shadow-lg hover:border-emerald-500/40 transition-all group flex items-center gap-4"
            >
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-800 flex items-center justify-center font-bold text-white font-mono text-base shadow-md group-hover:scale-105 transition-transform shrink-0 border border-emerald-400/30">
                {member.initials}
              </div>
              <div>
                <h4 className="text-base font-bold text-white group-hover:text-emerald-300 transition-colors">
                  {member.name}
                </h4>
                <p className="text-xs text-slate-400 mt-0.5">{member.role}</p>
                <span className="inline-block mt-1 text-[10px] font-mono text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/20">
                  EPICS 2026
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
