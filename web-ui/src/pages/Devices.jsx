import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Tv, Monitor, Smartphone, Wifi, WifiOff } from 'lucide-react';
import { useDevices, createDevice } from '../hooks/useApi';
import { PageHeader, LoadingState, EmptyState, Modal, Toast, Badge, StatusIndicator } from '../components/ui';

export default function Devices() {
  const { data: devices, loading, refetch } = useDevices();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newLocation, setNewLocation] = useState('');
  const [creating, setCreating] = useState(false);
  const [toast, setToast] = useState(null);
  
  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    
    setCreating(true);
    try {
      await createDevice({ name: newName, location: newLocation });
      setShowCreate(false);
      setNewName('');
      setNewLocation('');
      setToast({ message: 'Device created', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    } finally {
      setCreating(false);
    }
  };
  
  if (loading) {
    return <LoadingState message="Loading devices..." />;
  }
  
  return (
    <div>
      <PageHeader 
        title="Devices"
        description="Manage your digital signage displays"
        actions={
          <button onClick={() => setShowCreate(true)} className="btn btn-primary">
            <Plus className="w-4 h-4" />
            Add Device
          </button>
        }
      />
      
      {devices?.length === 0 ? (
        <EmptyState 
          icon={Tv}
          title="No devices yet"
          description="Add your first display device to get started"
          action={
            <button onClick={() => setShowCreate(true)} className="btn btn-primary">
              <Plus className="w-4 h-4" />
              Add Device
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {devices?.map(device => (
            <Link 
              key={device.id} 
              to={`/devices/${device.id}`}
              className="card p-6 hover:border-surface-600 transition-all group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-surface-800 rounded-xl group-hover:bg-accent/20 transition-colors">
                  {device.orientation === 'portrait' ? (
                    <Smartphone className="w-6 h-6 text-surface-400 group-hover:text-accent" />
                  ) : (
                    <Monitor className="w-6 h-6 text-surface-400 group-hover:text-accent" />
                  )}
                </div>
                <StatusIndicator online={device.is_online} showLabel />
              </div>
              
              <h3 className="font-semibold text-lg mb-1">{device.name}</h3>
              <p className="text-sm text-surface-500 mb-4">{device.location || 'No location set'}</p>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-surface-500">
                  Code: <span className="font-mono text-surface-300">{device.access_code}</span>
                </span>
                {device.schedule_group && (
                  <Badge color="blue">{device.schedule_group.name}</Badge>
                )}
              </div>
              
              {(device.flip_horizontal || device.flip_vertical) && (
                <div className="mt-3 flex gap-2">
                  {device.flip_horizontal && <Badge color="gray">Flip H</Badge>}
                  {device.flip_vertical && <Badge color="gray">Flip V</Badge>}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
      
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Add Device">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-2">Device Name *</label>
            <input 
              type="text" 
              value={newName} 
              onChange={e => setNewName(e.target.value)}
              placeholder="e.g., Lobby Display"
              className="input"
              autoFocus
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-2">Location</label>
            <input 
              type="text" 
              value={newLocation} 
              onChange={e => setNewLocation(e.target.value)}
              placeholder="e.g., Building A, Floor 1"
              className="input"
            />
          </div>
          
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-800">
            <button type="button" onClick={() => setShowCreate(false)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={creating || !newName.trim()}>
              {creating ? 'Creating...' : 'Create Device'}
            </button>
          </div>
        </form>
      </Modal>
      
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}