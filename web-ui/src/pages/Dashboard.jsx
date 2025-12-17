import React from 'react';
import { Link } from 'react-router-dom';
import { Tv, FolderOpen, Calendar, MonitorPlay, Wifi, WifiOff, ArrowRight } from 'lucide-react';
import { useStats, useDevices, useContentGroups, useScheduleGroups } from '../hooks/useApi';
import { PageHeader, StatCard, LoadingState, Badge, StatusIndicator, ColorDot } from '../components/ui';

export default function Dashboard() {
  const { data: stats, loading: statsLoading } = useStats();
  const { data: devices, loading: devicesLoading } = useDevices();
  const { data: contentGroups, loading: contentLoading } = useContentGroups();
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
          icon={FolderOpen} 
          label="Content Groups" 
          value={stats?.content_groups || 0}
          color="blue"
        />
        <StatCard 
          icon={Calendar} 
          label="Schedule Groups" 
          value={stats?.schedule_groups || 0}
          color="purple"
        />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Devices */}
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
        
        {/* Content Groups */}
        <div className="card">
          <div className="flex items-center justify-between px-6 py-4 border-b border-surface-800">
            <h2 className="font-semibold">Content Groups</h2>
            <Link to="/content" className="text-sm text-accent hover:text-accent-400 flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-surface-800">
            {contentLoading ? (
              <div className="p-6">
                <LoadingState />
              </div>
            ) : contentGroups?.length === 0 ? (
              <div className="p-6 text-center text-surface-400">
                No content groups created yet
              </div>
            ) : (
              contentGroups?.slice(0, 5).map(group => (
                <Link 
                  key={group.id} 
                  to={`/content/${group.id}`}
                  className="flex items-center gap-4 px-6 py-4 hover:bg-surface-800/50 transition-colors"
                >
                  <ColorDot color={group.color} size="lg" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{group.name}</p>
                    <p className="text-sm text-surface-500">{group.content_count} items</p>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
        
        {/* Schedule Groups */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between px-6 py-4 border-b border-surface-800">
            <h2 className="font-semibold">Schedule Groups</h2>
            <Link to="/schedules" className="text-sm text-accent hover:text-accent-400 flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
            {schedulesLoading ? (
              <div className="col-span-full">
                <LoadingState />
              </div>
            ) : scheduleGroups?.length === 0 ? (
              <div className="col-span-full text-center text-surface-400 py-6">
                No schedule groups created yet
              </div>
            ) : (
              scheduleGroups?.map(group => (
                <Link 
                  key={group.id} 
                  to={`/schedules/${group.id}`}
                  className="card-hover p-4"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <ColorDot color={group.color} size="lg" />
                    <span className="font-medium">{group.name}</span>
                    {group.is_active ? (
                      <Badge color="green">Active</Badge>
                    ) : (
                      <Badge color="gray">Inactive</Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-surface-400">
                    <span>{group.schedule_count} schedules</span>
                    <span>{group.device_count} devices</span>
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
