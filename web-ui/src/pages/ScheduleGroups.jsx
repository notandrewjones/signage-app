import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Calendar, Image, Tv } from 'lucide-react';
import { useScheduleGroups, createScheduleGroup } from '../hooks/useApi';
import { PageHeader, LoadingState, EmptyState, Modal, Toast, Badge, ColorDot } from '../components/ui';

export default function ScheduleGroups() {
  const { data: groups, loading, refetch } = useScheduleGroups();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newColor, setNewColor] = useState('#3B82F6');
  const [creating, setCreating] = useState(false);
  const [toast, setToast] = useState(null);
  
  const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];
  
  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    
    setCreating(true);
    try {
      await createScheduleGroup({ name: newName, description: newDescription, color: newColor });
      setShowCreate(false);
      setNewName('');
      setNewDescription('');
      setNewColor('#3B82F6');
      setToast({ message: 'Schedule group created', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    } finally {
      setCreating(false);
    }
  };
  
  if (loading) {
    return <LoadingState message="Loading schedule groups..." />;
  }
  
  return (
    <div>
      <PageHeader 
        title="Schedule Groups"
        description="Organize content and control when it plays"
        actions={
          <button onClick={() => setShowCreate(true)} className="btn btn-primary">
            <Plus className="w-4 h-4" />
            Create Group
          </button>
        }
      />
      
      {groups?.length === 0 ? (
        <EmptyState 
          icon={Calendar}
          title="No schedule groups yet"
          description="Create a schedule group to organize content and control playback times"
          action={
            <button onClick={() => setShowCreate(true)} className="btn btn-primary">
              <Plus className="w-4 h-4" />
              Create Group
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups?.map(group => (
            <Link 
              key={group.id} 
              to={`/schedules/${group.id}`}
              className="card p-6 hover:border-surface-600 transition-all group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <ColorDot color={group.color} size="lg" />
                  <div>
                    <h3 className="font-semibold text-lg">{group.name}</h3>
                    {group.description && (
                      <p className="text-sm text-surface-500 line-clamp-1">{group.description}</p>
                    )}
                  </div>
                </div>
                {group.is_active ? (
                  <Badge color="green">Active</Badge>
                ) : (
                  <Badge color="gray">Inactive</Badge>
                )}
              </div>
              
              <div className="grid grid-cols-3 gap-4 pt-4 border-t border-surface-800">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-surface-500 mb-1">
                    <Image className="w-4 h-4" />
                  </div>
                  <p className="text-lg font-semibold">{group.content_count}</p>
                  <p className="text-xs text-surface-500">Content</p>
                </div>
                
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-surface-500 mb-1">
                    <Calendar className="w-4 h-4" />
                  </div>
                  <p className="text-lg font-semibold">{group.schedule_count}</p>
                  <p className="text-xs text-surface-500">Schedules</p>
                </div>
                
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-surface-500 mb-1">
                    <Tv className="w-4 h-4" />
                  </div>
                  <p className="text-lg font-semibold">{group.device_count}</p>
                  <p className="text-xs text-surface-500">Devices</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
      
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create Schedule Group">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-2">Name *</label>
            <input 
              type="text" 
              value={newName} 
              onChange={e => setNewName(e.target.value)}
              placeholder="e.g., Morning Announcements"
              className="input"
              autoFocus
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-2">Description</label>
            <textarea 
              value={newDescription} 
              onChange={e => setNewDescription(e.target.value)}
              placeholder="Optional description"
              className="input min-h-[80px]"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-surface-300 mb-2">Color</label>
            <div className="flex gap-2">
              {colors.map(c => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setNewColor(c)}
                  className={`w-8 h-8 rounded-full transition-transform ${
                    newColor === c ? 'ring-2 ring-white ring-offset-2 ring-offset-surface-900 scale-110' : ''
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
          </div>
          
          <div className="flex justify-end gap-3 pt-4 border-t border-surface-800">
            <button type="button" onClick={() => setShowCreate(false)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={creating || !newName.trim()}>
              {creating ? 'Creating...' : 'Create Group'}
            </button>
          </div>
        </form>
      </Modal>
      
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}