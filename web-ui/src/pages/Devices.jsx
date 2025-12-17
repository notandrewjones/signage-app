import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Tv, MapPin, Wifi, WifiOff, MoreVertical, Trash2, Edit, Key, Copy, Check } from 'lucide-react';
import { useDevices, createDevice, deleteDevice } from '../hooks/useApi';
import { PageHeader, LoadingState, EmptyState, Modal, ConfirmDialog, StatusIndicator, Toast } from '../components/ui';

export default function Devices() {
  const { data: devices, loading, refetch } = useDevices();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [toast, setToast] = useState(null);
  const navigate = useNavigate();
  
  const handleCreate = async (data) => {
    try {
      const device = await createDevice(data);
      setShowCreateModal(false);
      setToast({ message: 'Device created successfully', type: 'success' });
      refetch();
      navigate(`/devices/${device.id}`);
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleDelete = async (id) => {
    try {
      await deleteDevice(id);
      setToast({ message: 'Device deleted', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  if (loading) {
    return <LoadingState message="Loading devices..." />;
  }
  
  return (
    <div>
      <PageHeader 
        title="Devices" 
        description="Manage your display devices"
        actions={
          <button 
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            <Plus className="w-5 h-5" />
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
            <button 
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary"
            >
              <Plus className="w-5 h-5" />
              Add Device
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {devices.map(device => (
            <DeviceCard 
              key={device.id} 
              device={device} 
              onDelete={() => setDeleteConfirm(device)}
            />
          ))}
        </div>
      )}
      
      <CreateDeviceModal 
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreate}
      />
      
      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => handleDelete(deleteConfirm.id)}
        title="Delete Device"
        message={`Are you sure you want to delete "${deleteConfirm?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        danger
      />
      
      {toast && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast(null)} 
        />
      )}
    </div>
  );
}

function DeviceCard({ device, onDelete }) {
  const [showMenu, setShowMenu] = useState(false);
  
  return (
    <div className="card-hover relative">
      <Link to={`/devices/${device.id}`} className="block p-5">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-surface-800 rounded-xl">
              <Tv className="w-6 h-6 text-surface-400" />
            </div>
            <div>
              <h3 className="font-semibold">{device.name}</h3>
              {device.location && (
                <div className="flex items-center gap-1 text-sm text-surface-500">
                  <MapPin className="w-3 h-3" />
                  {device.location}
                </div>
              )}
            </div>
          </div>
          <StatusIndicator online={device.is_online} />
        </div>
        
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between text-surface-400">
            <span>Content Groups</span>
            <span className="text-surface-200">{device.content_groups?.length || 0}</span>
          </div>
          <div className="flex items-center justify-between text-surface-400">
            <span>Schedule</span>
            <span className="text-surface-200">{device.schedule_group?.name || 'None'}</span>
          </div>
          {device.last_seen && (
            <div className="flex items-center justify-between text-surface-400">
              <span>Last seen</span>
              <span className="text-surface-200">
                {new Date(device.last_seen).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </Link>
      
      <div className="absolute top-4 right-4">
        <button 
          onClick={(e) => { e.preventDefault(); setShowMenu(!showMenu); }}
          className="btn-ghost p-2 rounded-lg"
        >
          <MoreVertical className="w-4 h-4" />
        </button>
        
        {showMenu && (
          <>
            <div 
              className="fixed inset-0 z-10" 
              onClick={() => setShowMenu(false)} 
            />
            <div className="absolute right-0 top-full mt-1 w-40 bg-surface-800 border border-surface-700 rounded-lg shadow-xl z-20 py-1">
              <Link 
                to={`/devices/${device.id}`}
                className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-surface-700 transition-colors"
              >
                <Edit className="w-4 h-4" />
                Edit
              </Link>
              <button 
                onClick={(e) => { e.preventDefault(); setShowMenu(false); onDelete(); }}
                className="flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-surface-700 transition-colors w-full"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function CreateDeviceModal({ isOpen, onClose, onCreate }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    
    setLoading(true);
    await onCreate({ name, description, location });
    setLoading(false);
    setName('');
    setDescription('');
    setLocation('');
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add New Device">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">
            Device Name *
          </label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g., Lobby Display 1"
            className="input"
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">
            Location
          </label>
          <input
            type="text"
            value={location}
            onChange={e => setLocation(e.target.value)}
            placeholder="e.g., Building A, Floor 1"
            className="input"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">
            Description
          </label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="Optional notes about this device"
            className="input min-h-[80px]"
          />
        </div>
        
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading || !name.trim()}>
            {loading ? 'Creating...' : 'Create Device'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
