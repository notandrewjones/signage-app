import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Tv, 
  Calendar, 
  Image as ImageIcon
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/devices', icon: Tv, label: 'Devices' },
  { to: '/schedules', icon: Calendar, label: 'Schedules' },
  { to: '/splash-screen', icon: ImageIcon, label: 'Splash Screen' },
];

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 bg-surface-900 border-r border-surface-800 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-surface-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-accent to-purple-500 rounded-xl flex items-center justify-center">
            <Tv className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight">Signage</h1>
            <p className="text-xs text-surface-500">Control Panel</p>
          </div>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `
              flex items-center gap-3 px-4 py-3 rounded-xl transition-all
              ${isActive 
                ? 'bg-accent/10 text-accent' 
                : 'text-surface-400 hover:text-surface-100 hover:bg-surface-800'
              }
            `}
          >
            <Icon className="w-5 h-5" />
            <span className="font-medium">{label}</span>
          </NavLink>
        ))}
      </nav>
      
      {/* Footer */}
      <div className="p-4 border-t border-surface-800">
        <div className="flex items-center gap-3 px-4 py-3 text-surface-500 text-sm">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span>Server Online</span>
        </div>
      </div>
    </aside>
  );
}