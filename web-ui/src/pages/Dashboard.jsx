import React from 'react';
import { Link } from 'react-router-dom';
import { Tv, Calendar, MonitorPlay, Wifi, Image as ImageIcon, ArrowRight } from 'lucide-react';
import { useStats, useDevices, useScheduleGroups } from '../hooks/useApi';
import { PageHeader, StatCard, LoadingState, Badge, StatusIndicator, ColorDot } from '../components/ui';

export default function Dashboard() {
  const { data: stats, loading: statsLoading } = useStats();
  const { data: devices, loading: devicesLoading } = useDevices();
  const { data: scheduleGroups, loading: schedulesLoading } = useScheduleGroups();
  
  if (statsLoading) {
    return <LoadingState message="Loading dashboard..." />;
  }
  
  return (
    <div>
      <PageHeader 
        title="Dashboard" 
        description="Overview of your digital signage system"
      />
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard 
          icon={Tv} 
          label="Total Devices" 
          value={stats?.total_devices || 0}
          color="accent"
        />
        <StatCard 
          icon={Wifi} 
          label="Online Now" 
          value={stats?.online_devices || 0}
          color="green"
        />
        <StatCard 
          icon={Calendar} 
          label="Schedule Groups" 
          value={stats?.schedule_groups || 0}
          color="blue"
        />
        <StatCard 
          icon={ImageIcon} 
          label="Total Content" 
          value={stats?.total_content || 0}
          color="purple"
        />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Devices */}
        <div className="card">
          <div className="flex items-center justify-between px-6 py-4 border-b border-surface-800">
            <h2 className="font-semibold">Devices</h2>
            <Link to="/devices" className="text-sm text-accent hover:text-accent-400 flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-surface-800">
            {devicesLoading ? (
              <div className="p-6">
                <LoadingState />
              </div>
            ) : devices?.length === 0 ? (
              <div className="p-6 text-center text-surface-400">
                No devices configured yet
              </div>
            ) : (
              devices?.slice(0, 5).map(device => (
                <Link 
                  key={device.id} 
                  to={`/devices/${device.id}`}
                  className="flex items-center gap-4 px-6 py-4 hover:bg-surface-800/50 transition-colors"
                >
                  <div className="p-2 bg-surface-800 rounded-lg">
                    <MonitorPlay className="w-5 h-5 text-surface-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{device.name}</p>
                    <p className="text-sm text-surface-500 truncate">{device.location || 'No location set'}</p>
                  </div>
                  <StatusIndicator online={device.is_online} />
                </Link>
              ))
            )}
          </div>
        </div>
        
        {/* Schedule Groups */}
        <div className="card">
          <div className="flex items-center justify-between px-6 py-4 border-b border-surface-800">
            <h2 className="font-semibold">Schedule Groups</h2>
            <Link to="/schedules" className="text-sm text-accent hover:text-accent-400 flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-surface-800">
            {schedulesLoading ? (
              <div className="p-6">
                <LoadingState />
              </div>
            ) : scheduleGroups?.length === 0 ? (
              <div className="p-6 text-center text-surface-400">
                No schedule groups created yet
              </div>
            ) : (
              scheduleGroups?.slice(0, 5).map(group => (
                <Link 
                  key={group.id} 
                  to={`/schedules/${group.id}`}
                  className="flex items-center gap-4 px-6 py-4 hover:bg-surface-800/50 transition-colors"
                >
                  <ColorDot color={group.color} size="lg" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium truncate">{group.name}</p>
                      {group.is_active ? (
                        <Badge color="green">Active</Badge>
                      ) : (
                        <Badge color="gray">Inactive</Badge>
                      )}
                    </div>
                    <p className="text-sm text-surface-500">
                      {group.content_count} items • {group.device_count} devices
                    </p>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}