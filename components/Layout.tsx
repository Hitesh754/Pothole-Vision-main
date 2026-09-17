import React from 'react';
import { 
  LayoutDashboard, 
  Camera, 
  FileCheck2, 
  Map, 
  Users, 
  ShieldAlert, 
  Leaf, 
  Locate,
  Activity
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onLocate?: () => void;
  ticketCount?: number;
}

export const Layout: React.FC<LayoutProps> = ({ 
  children, 
  activeTab, 
  setActiveTab, 
  onLocate,
  ticketCount = 0
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Admin Dashboard', icon: LayoutDashboard },
    { id: 'vision', label: 'Civic AI Scanner', icon: Camera, badge: 'AI Vision' },
    { id: 'tickets', label: 'Govt Grievances', icon: FileCheck2, count: ticketCount },
    { id: 'heatmap', label: 'Damage Heatmap', icon: Map },
    { id: 'team', label: 'EPICS Project Info', icon: Users },
  ];

  return (
    <div className="flex h-screen bg-[#020617] font-sans text-slate-100 overflow-hidden select-none">
      {/* Sidebar (Desktop) */}
      <aside className="w-64 bg-[#0a1b14] border-r border-emerald-950/60 text-white flex-shrink-0 hidden md:flex flex-col shadow-2xl z-30">
        {/* Brand Header */}
        <div className="p-5 border-b border-emerald-900/30 bg-gradient-to-b from-[#0F382A]/70 to-transparent">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center font-extrabold text-white shadow-[0_0_20px_rgba(16,185,129,0.4)] border border-emerald-400/30">
              <Leaf size={20} className="text-emerald-100" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                CivicVision <span className="text-emerald-400 font-mono text-xs px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/40">AI</span>
              </h1>
              <p className="text-[10px] uppercase tracking-wider text-emerald-400/80 font-mono mt-0.5">Govt of India • Civic Grievance</p>
            </div>
          </div>
          
          {/* Tagline */}
          <p className="text-[11px] text-slate-400 mt-3 leading-relaxed border-t border-emerald-900/30 pt-2 font-normal">
            Citizen civic issue scanner & direct Govt of India grievance dispatch (CPGRAMS / NHAI / MoHUA).
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3.5 space-y-1.5 overflow-y-auto">
          <div className="text-[10px] font-mono tracking-widest text-slate-500 px-3 uppercase mb-1">
            System Modules
          </div>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 text-white shadow-[0_4px_16px_rgba(16,185,129,0.35)] border border-emerald-400/30'
                    : 'text-slate-300 hover:bg-emerald-950/40 hover:text-emerald-200'
                }`}
              >
                <div className="flex items-center gap-3">
                  <item.icon size={18} className={isActive ? 'text-emerald-100' : 'text-slate-400'} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] font-mono bg-emerald-900/70 text-emerald-300 border border-emerald-500/30 px-1.5 py-0.5 rounded-full">
                    {item.badge}
                  </span>
                )}
                {typeof item.count === 'number' && item.count > 0 && (
                  <span className="text-[11px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30 px-1.5 py-0.5 rounded-full font-bold">
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}

          {/* Quick Action: Auto-Locate */}
          {onLocate && (
            <div className="pt-4 border-t border-emerald-900/30">
              <button
                onClick={onLocate}
                className="w-full flex items-center gap-2.5 px-3.5 py-2.5 text-xs font-semibold rounded-xl text-emerald-300 bg-emerald-950/50 hover:bg-emerald-900/50 border border-emerald-700/40 transition-all shadow-sm"
              >
                <Locate size={15} className="text-emerald-400 animate-pulse" />
                <span>Geotag Current GPS</span>
              </button>
            </div>
          )}
        </nav>

        {/* Footer Info */}
        <div className="p-4 border-t border-emerald-900/30 bg-[#07130e] text-xs text-slate-400">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              Live Inference
            </span>
            <span className="text-emerald-400 font-bold">YOLOv8</span>
          </div>
          <p className="text-[10px] text-slate-400 mt-1">Supervised by Dr. M. Suresh</p>
        </div>
      </aside>

      {/* Mobile Header (Top) */}
      <div className="md:hidden fixed top-0 w-full bg-[#0a1b14]/95 backdrop-blur-md text-white z-40 px-4 flex justify-between items-center border-b border-emerald-900/40 h-14">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center font-bold text-white shadow-md">
            <Leaf size={16} />
          </div>
          <span className="font-bold text-base tracking-tight">RoadSense AI</span>
        </div>
        <span className="text-[10px] font-mono bg-emerald-900/80 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full">
          EPICS 2026
        </span>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-7 pt-16 md:pt-7 w-full bg-[#030a07] relative">
        <div className="max-w-7xl mx-auto min-h-[calc(100vh-6rem)]">
          {children}
        </div>
      </main>

      {/* Mobile Bottom Navigation Bar */}
      <nav className="md:hidden fixed bottom-0 w-full bg-[#0a1b14]/95 backdrop-blur-xl border-t border-emerald-900/40 z-50 px-2 shadow-2xl">
        <div className="flex justify-around items-center h-16 pb-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex flex-col items-center justify-center w-full h-full space-y-1 transition-all ${
                  isActive ? 'text-emerald-400' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <item.icon size={19} strokeWidth={isActive ? 2.5 : 2} />
                <span className="text-[10px] font-medium">{item.label.split(' ')[0]}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
};