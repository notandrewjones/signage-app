import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Devices from './pages/Devices';
import DeviceDetail from './pages/DeviceDetail';
import ContentGroups from './pages/ContentGroups';
import ContentGroupDetail from './pages/ContentGroupDetail';
import ScheduleGroups from './pages/ScheduleGroups';
import ScheduleGroupDetail from './pages/ScheduleGroupDetail';
import DisplaySettings from './pages/DisplaySettings';

export default function App() {
  return (
    <div className="min-h-screen bg-surface-950">
      <Sidebar />
      <main className="ml-64 p-8">
        <div className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/devices" element={<Devices />} />
            <Route path="/devices/:id" element={<DeviceDetail />} />
            <Route path="/content" element={<ContentGroups />} />
            <Route path="/content/:id" element={<ContentGroupDetail />} />
            <Route path="/schedules" element={<ScheduleGroups />} />
            <Route path="/schedules/:id" element={<ScheduleGroupDetail />} />
            <Route path="/display-settings" element={<DisplaySettings />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
