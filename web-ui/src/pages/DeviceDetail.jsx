import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Save, Trash2, RefreshCw, Copy, Check, Monitor, Smartphone, FlipHorizontal, FlipVertical } from 'lucide-react';
import { useDevice, useScheduleGroups, updateDevice, deleteDevice, regenerateAccessCode } from '../hooks/useApi';
import { PageHeader, LoadingState, ConfirmDialog, Toast, Select, Badge, ColorDot } from '../components/ui';

export default function DeviceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: device, loading, refetch } = useDevice(id);
  const { data: scheduleGroups } = useScheduleGroups();
  
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [scheduleGroupId, setScheduleGroupId] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [orientation, setOrientation] = useState('landscape');
  const [flipHorizontal, setFlipHorizontal] = useState(false);
  const [flipVertical, setFlipVertical] = useState(false);
  
  const [saving, setSaving] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [codeConfirm, setCodeConfirm] = useState(false);
  const [copied, setCopied] = useState(false);
  const [toast, setToast] = useState(null);
  const [initialized, setInitialized] = useState(false);
  
  React.useEffect(() => {
    if (device && !initialized) {
      setName(device.name);
      setLocation(device.location || '');
      setDescription(device.description || '');
      setScheduleGroupId(device.schedule_group_id?.toString() || '');
      setIsActive(device.is_active);
      setOrientation(device.orientation || 'landscape');
      setFlipHorizontal(device.flip_horizontal || false);
      setFlipVertical(device.flip_vertical || false);
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
        orientation,
        flip_horizontal: flipHorizontal,
        flip_vertical: flipVertical,
        schedule_group_id: scheduleGroupId ? parseInt(scheduleGroupId) : null,
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
  
  const handleRegenerateCode = async () => {
    try {
      await regenerateAccessCode(id);
      setToast({ message: 'Access code regenerated', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const copyAccessCode = () => {
    navigator.clipboard.writeText(device.access_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
      
      {/* Access Code Card - Prominent at top */}
      <div className="card p-6 mb-6 bg-gradient-to-br from-accent/10 to-purple-500/10 border-accent/20">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-sm font-medium text-surface-400 mb-1">Access Code</h2>
            <p className="text-xs text-surface-500 mb-3">Enter this code in the player app to connect</p>
            <div className="flex items-center gap-4">
              <span className="text-5xl font-bold font-mono tracking-[0.3em] text-accent">
                {device.access_code}
              </span>
              <button 
                onClick={copyAccessCode}
                className="btn btn-secondary"
                title="Copy to clipboard"
              >
                {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>
          <div className="text-right">
            {device.is_registered ? (
              <Badge color="green">Connected</Badge>
            ) : (
              <Badge color="yellow">Waiting for player</Badge>
            )}
            <button 
              onClick={() => setCodeConfirm(true)}
              className="btn btn-ghost text-sm mt-3 block"
            >
              <RefreshCw className="w-3 h-3 mr-1 inline" />
              Generate new code
            </button>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="section-title">Device Information</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-surface-300 mb-2">Device Name *</label>
                <input type="text" value={name} onChange={e => setName(e.target.value)} className="input" />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-surface-300 mb-2">Location</label>
                <input type="text" value={location} onChange={e => setLocation(e.target.value)} placeholder="e.g., Building A, Floor 1" className="input" />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-surface-300 mb-2">Description</label>
                <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Optional notes" className="input min-h-[80px]" />
              </div>
              
              <div className="flex items-center gap-3">
                <input type="checkbox" id="isActive" checked={isActive} onChange={e => setIsActive(e.target.checked)} />
                <label htmlFor="isActive" className="text-sm">Device is active</label>
              </div>
            </div>
          </div>
          
          {/* Display Orientation Settings */}
          <div className="card p-6">
            <h2 className="section-title">Display Orientation</h2>
            <p className="text-sm text-surface-400 mb-6">Configure how content is displayed on this device</p>
            
            {/* Orientation Toggle */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-surface-300 mb-3">Screen Orientation</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setOrientation('landscape')}
                  className={`flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                    orientation === 'landscape' 
                      ? 'border-accent bg-accent/10' 
                      : 'border-surface-700 hover:border-surface-600'
                  }`}
                >
                  <div className={`w-20 h-12 rounded-lg border-2 flex items-center justify-center ${
                    orientation === 'landscape' ? 'border-accent bg-accent/20' : 'border-surface-600 bg-surface-800'
                  }`}>
                    <Monitor className={`w-6 h-6 ${orientation === 'landscape' ? 'text-accent' : 'text-surface-500'}`} />
                  </div>
                  <span className={`text-sm font-medium ${orientation === 'landscape' ? 'text-accent' : 'text-surface-400'}`}>
                    Landscape
                  </span>
                </button>
                
                <button
                  type="button"
                  onClick={() => setOrientation('portrait')}
                  className={`flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                    orientation === 'portrait' 
                      ? 'border-accent bg-accent/10' 
                      : 'border-surface-700 hover:border-surface-600'
                  }`}
                >
                  <div className={`w-12 h-20 rounded-lg border-2 flex items-center justify-center ${
                    orientation === 'portrait' ? 'border-accent bg-accent/20' : 'border-surface-600 bg-surface-800'
                  }`}>
                    <Smartphone className={`w-6 h-6 ${orientation === 'portrait' ? 'text-accent' : 'text-surface-500'}`} />
                  </div>
                  <span className={`text-sm font-medium ${orientation === 'portrait' ? 'text-accent' : 'text-surface-400'}`}>
                    Portrait
                  </span>
                </button>
              </div>
            </div>
            
            {/* Flip Options */}
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-3">Flip Options</label>
              <p className="text-xs text-surface-500 mb-4">Use these if your display is mounted upside down or mirrored</p>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFlipHorizontal(!flipHorizontal)}
                  className={`flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                    flipHorizontal 
                      ? 'border-accent bg-accent/10' 
                      : 'border-surface-700 hover:border-surface-600'
                  }`}
                >
                  <div className={`p-2 rounded-lg ${flipHorizontal ? 'bg-accent/20' : 'bg-surface-800'}`}>
                    <FlipHorizontal className={`w-5 h-5 ${flipHorizontal ? 'text-accent' : 'text-surface-500'}`} />
                  </div>
                  <div className="text-left">
                    <p className={`text-sm font-medium ${flipHorizontal ? 'text-accent' : 'text-surface-300'}`}>
                      Flip Horizontal
                    </p>
                    <p className="text-xs text-surface-500">Mirror left to right</p>
                  </div>
                </button>
                
                <button
                  type="button"
                  onClick={() => setFlipVertical(!flipVertical)}
                  className={`flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                    flipVertical 
                      ? 'border-accent bg-accent/10' 
                      : 'border-surface-700 hover:border-surface-600'
                  }`}
                >
                  <div className={`p-2 rounded-lg ${flipVertical ? 'bg-accent/20' : 'bg-surface-800'}`}>
                    <FlipVertical className={`w-5 h-5 ${flipVertical ? 'text-accent' : 'text-surface-500'}`} />
                  </div>
                  <div className="text-left">
                    <p className={`text-sm font-medium ${flipVertical ? 'text-accent' : 'text-surface-300'}`}>
                      Flip Vertical
                    </p>
                    <p className="text-xs text-surface-500">Mirror top to bottom</p>
                  </div>
                </button>
              </div>
            </div>
            
            {/* Preview */}
            <div className="mt-6 p-4 bg-surface-800 rounded-xl">
              <p className="text-xs text-surface-500 mb-3 text-center">Preview</p>
              <div className="flex justify-center">
                <div 
                  className={`border-2 border-surface-600 rounded-lg bg-surface-900 flex items-center justify-center text-surface-500 text-xs ${
                    orientation === 'landscape' ? 'w-32 h-20' : 'w-20 h-32'
                  }`}
                  style={{
                    transform: `${flipHorizontal ? 'scaleX(-1)' : ''} ${flipVertical ? 'scaleY(-1)' : ''}`.trim() || 'none'
                  }}
                >
                  <span style={{ transform: `${flipHorizontal ? 'scaleX(-1)' : ''} ${flipVertical ? 'scaleY(-1)' : ''}`.trim() || 'none' }}>
                    Content
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="card p-6">
            <h2 className="section-title">Schedule Group</h2>
            <p className="text-sm text-surface-400 mb-4">Assign this device to a schedule group to display content</p>
            <Select
              value={scheduleGroupId}
              onChange={setScheduleGroupId}
              placeholder="No schedule group"
              options={scheduleGroups?.map(g => ({ value: g.id.toString(), label: g.name })) || []}
            />
            {scheduleGroupId && scheduleGroups && (
              <div className="mt-3">
                <Link 
                  to={`/schedules/${scheduleGroupId}`}
                  className="text-sm text-accent hover:text-accent-400"
                >
                  View schedule group →
                </Link>
              </div>
            )}
          </div>
        </div>
        
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
            <h2 className="section-title">Current Settings</h2>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-surface-400">Orientation</span>
                <Badge color={orientation === 'landscape' ? 'blue' : 'purple'}>
                  {orientation}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-surface-400">Flip H</span>
                <span>{flipHorizontal ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-surface-400">Flip V</span>
                <span>{flipVertical ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <ConfirmDialog isOpen={deleteConfirm} onClose={() => setDeleteConfirm(false)} onConfirm={handleDelete} title="Delete Device" message="Are you sure you want to delete this device?" confirmText="Delete" danger />
      <ConfirmDialog isOpen={codeConfirm} onClose={() => setCodeConfirm(false)} onConfirm={handleRegenerateCode} title="Generate New Access Code" message="This will disconnect any connected player. You'll need to enter the new code on the player." confirmText="Generate" />
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}