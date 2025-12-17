import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Save, Trash2, Key, Copy, Check, Tv, MapPin, Wifi, Clock, Monitor } from 'lucide-react';
import { useDevice, useContentGroups, useScheduleGroups, updateDevice, deleteDevice, regenerateDeviceKey } from '../hooks/useApi';
import { PageHeader, LoadingState, ConfirmDialog, Toast, Select, Badge, ColorDot } from '../components/ui';

export default function DeviceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: device, loading, refetch } = useDevice(id);
  const { data: contentGroups } = useContentGroups();
  const { data: scheduleGroups } = useScheduleGroups();
  
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [scheduleGroupId, setScheduleGroupId] = useState('');
  const [selectedContentGroups, setSelectedContentGroups] = useState([]);
  const [isActive, setIsActive] = useState(true);
  
  const [saving, setSaving] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [keyConfirm, setKeyConfirm] = useState(false);
  const [copied, setCopied] = useState(false);
  const [toast, setToast] = useState(null);
  const [initialized, setInitialized] = useState(false);
  
  // Initialize form when device loads
  React.useEffect(() => {
    if (device && !initialized) {
      setName(device.name);
      setLocation(device.location || '');
      setDescription(device.description || '');
      setScheduleGroupId(device.schedule_group_id?.toString() || '');
      setSelectedContentGroups(device.content_groups?.map(g => g.id) || []);
      setIsActive(device.is_active);
      setInitialized(true);
    }
  }, [device, initialized]);
  
  const handleSave = async () => {
    setSaving(true);
    try {
      await updateDevice(id, {
        name,
        location,
        description,
        is_active: isActive,
        schedule_group_id: scheduleGroupId ? parseInt(scheduleGroupId) : null,
        content_group_ids: selectedContentGroups,
      });
      setToast({ message: 'Device updated successfully', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    } finally {
      setSaving(false);
    }
  };
  
  const handleDelete = async () => {
    try {
      await deleteDevice(id);
      navigate('/devices');
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleRegenerateKey = async () => {
    try {
      await regenerateDeviceKey(id);
      setToast({ message: 'Device key regenerated', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const copyDeviceKey = () => {
    navigator.clipboard.writeText(device.device_key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const toggleContentGroup = (groupId) => {
    setSelectedContentGroups(prev => 
      prev.includes(groupId) 
        ? prev.filter(id => id !== groupId)
        : [...prev, groupId]
    );
  };
  
  if (loading || !device) {
    return <LoadingState message="Loading device..." />;
  }
  
  return (
    <div>
      <div className="mb-6">
        <Link to="/devices" className="inline-flex items-center gap-2 text-surface-400 hover:text-surface-200 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back to Devices
        </Link>
      </div>
      
      <PageHeader 
        title={device.name}
        description={device.location}
        actions={
          <div className="flex items-center gap-3">
            <button onClick={() => setDeleteConfirm(true)} className="btn btn-danger">
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
            <button onClick={handleSave} className="btn btn-primary" disabled={saving}>
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        }
      />
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Settings */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="section-title">Device Information</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-surface-300 mb-2">
                  Device Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="input"
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
                  placeholder="Optional notes"
                  className="input min-h-[80px]"
                />
              </div>
              
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="isActive"
                  checked={isActive}
                  onChange={e => setIsActive(e.target.checked)}
                />
                <label htmlFor="isActive" className="text-sm">
                  Device is active
                </label>
              </div>
            </div>
          </div>
          
          <div className="card p-6">
            <h2 className="section-title">Schedule Group</h2>
            <p className="text-sm text-surface-400 mb-4">
              Assign this device to a schedule group to control when content plays
            </p>
            <Select
              value={scheduleGroupId}
              onChange={setScheduleGroupId}
              placeholder="No schedule group"
              options={scheduleGroups?.map(g => ({ value: g.id.toString(), label: g.name })) || []}
            />
          </div>
          
          <div className="card p-6">
            <h2 className="section-title">Content Groups</h2>
            <p className="text-sm text-surface-400 mb-4">
              Select which content groups this device should display. Content from selected groups will play when no schedule is active.
            </p>
            
            {contentGroups?.length === 0 ? (
              <p className="text-surface-500 text-center py-4">
                No content groups available. <Link to="/content" className="text-accent">Create one</Link>
              </p>
            ) : (
              <div className="space-y-2">
                {contentGroups?.map(group => (
                  <label 
                    key={group.id}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedContentGroups.includes(group.id)
                        ? 'border-accent bg-accent/5'
                        : 'border-surface-700 hover:border-surface-600'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedContentGroups.includes(group.id)}
                      onChange={() => toggleContentGroup(group.id)}
                    />
                    <ColorDot color={group.color} />
                    <span className="flex-1">{group.name}</span>
                    <span className="text-sm text-surface-400">{group.content_count} items</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* Sidebar */}
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="section-title">Status</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-surface-400">Online</span>
                <div className="flex items-center gap-2">
                  <span className={`status-dot ${device.is_online ? 'status-online' : 'status-offline'}`} />
                  <span>{device.is_online ? 'Yes' : 'No'}</span>
                </div>
              </div>
              
              {device.ip_address && (
                <div className="flex items-center justify-between">
                  <span className="text-surface-400">IP Address</span>
                  <span className="font-mono text-sm">{device.ip_address}</span>
                </div>
              )}
              
              {device.screen_width && device.screen_height && (
                <div className="flex items-center justify-between">
                  <span className="text-surface-400">Resolution</span>
                  <span>{device.screen_width}x{device.screen_height}</span>
                </div>
              )}
              
              {device.last_seen && (
                <div className="flex items-center justify-between">
                  <span className="text-surface-400">Last Seen</span>
                  <span className="text-sm">{new Date(device.last_seen).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
          
          <div className="card p-6">
            <h2 className="section-title">Device Key</h2>
            <p className="text-sm text-surface-400 mb-4">
              Use this key to connect a player device
            </p>
            
            <div className="flex items-center gap-2 p-3 bg-surface-800 rounded-lg font-mono text-sm mb-4">
              <span className="flex-1 truncate">{device.device_key}</span>
              <button 
                onClick={copyDeviceKey}
                className="btn-ghost p-2 rounded-lg"
                title="Copy to clipboard"
              >
                {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
            
            <button 
              onClick={() => setKeyConfirm(true)}
              className="btn btn-secondary w-full"
            >
              <Key className="w-4 h-4" />
              Regenerate Key
            </button>
          </div>
        </div>
      </div>
      
      <ConfirmDialog
        isOpen={deleteConfirm}
        onClose={() => setDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="Delete Device"
        message="Are you sure you want to delete this device? This action cannot be undone."
        confirmText="Delete"
        danger
      />
      
      <ConfirmDialog
        isOpen={keyConfirm}
        onClose={() => setKeyConfirm(false)}
        onConfirm={handleRegenerateKey}
        title="Regenerate Device Key"
        message="Regenerating the key will disconnect any currently connected player. You'll need to update the player with the new key."
        confirmText="Regenerate"
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
