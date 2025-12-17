import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Calendar, MoreVertical, Trash2, Edit, Clock, Tv } from 'lucide-react';
import { useScheduleGroups, createScheduleGroup, deleteScheduleGroup } from '../hooks/useApi';
import { PageHeader, LoadingState, EmptyState, Modal, ConfirmDialog, Toast, ColorDot, Badge } from '../components/ui';

export default function ScheduleGroups() {
  const { data: groups, loading, refetch } = useScheduleGroups();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [toast, setToast] = useState(null);
  const navigate = useNavigate();
  
  const handleCreate = async (data) => {
    try {
      const group = await createScheduleGroup(data);
      setShowCreateModal(false);
      setToast({ message: 'Schedule group created', type: 'success' });
      refetch();
      navigate(`/schedules/${group.id}`);
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleDelete = async (id) => {
    try {
      await deleteScheduleGroup(id);
      setToast({ message: 'Schedule group deleted', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  if (loading) {
    return <LoadingState message="Loading schedule groups..." />;
  }
  
  return (
    <div>
      <PageHeader 
        title="Schedules" 
        description="Control when content plays on your devices"
        actions={
          <button 
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            <Plus className="w-5 h-5" />
            New Schedule Group
          </button>
        }
      />
      
      {groups?.length === 0 ? (
        <EmptyState
          icon={Calendar}
          title="No schedule groups"
          description="Create schedule groups to control when content plays"
          action={
            <button 
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary"
            >
              <Plus className="w-5 h-5" />
              New Schedule Group
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups.map(group => (
            <ScheduleGroupCard 
              key={group.id} 
              group={group} 
              onDelete={() => setDeleteConfirm(group)}
            />
          ))}
        </div>
      )}
      
      <CreateScheduleGroupModal 
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreate}
      />
      
      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => handleDelete(deleteConfirm.id)}
        title="Delete Schedule Group"
        message={`Are you sure you want to delete "${deleteConfirm?.name}"? All schedules in this group will be deleted.`}
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

function ScheduleGroupCard({ group, onDelete }) {
  const [showMenu, setShowMenu] = useState(false);
  
  return (
    <div className="card-hover relative">
      <Link to={`/schedules/${group.id}`} className="block p-5">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div 
              className="p-3 rounded-xl"
              style={{ backgroundColor: `${group.color}20` }}
            >
              <Calendar className="w-6 h-6" style={{ color: group.color }} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold">{group.name}</h3>
                {group.is_active ? (
                  <Badge color="green">Active</Badge>
                ) : (
                  <Badge color="gray">Inactive</Badge>
                )}
              </div>
              {group.description && (
                <p className="text-sm text-surface-500 line-clamp-1">
                  {group.description}
                </p>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2 text-surface-400">
            <Clock className="w-4 h-4" />
            <span>{group.schedule_count} schedule{group.schedule_count !== 1 ? 's' : ''}</span>
          </div>
          <div className="flex items-center gap-2 text-surface-400">
            <Tv className="w-4 h-4" />
            <span>{group.device_count} device{group.device_count !== 1 ? 's' : ''}</span>
          </div>
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
                to={`/schedules/${group.id}`}
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

function CreateScheduleGroupModal({ isOpen, onClose, onCreate }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [color, setColor] = useState('#10B981');
  const [loading, setLoading] = useState(false);
  
  const colors = [
    '#10B981', '#3B82F6', '#F59E0B', '#EF4444', 
    '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'
  ];
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    
    setLoading(true);
    await onCreate({ name, description, color });
    setLoading(false);
    setName('');
    setDescription('');
    setColor('#10B981');
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Schedule Group">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">
            Group Name *
          </label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g., Business Hours"
            className="input"
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">
            Description
          </label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="Optional description"
            className="input min-h-[80px]"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">
            Color
          </label>
          <div className="flex items-center gap-2">
            {colors.map(c => (
              <button
                key={c}
                type="button"
                onClick={() => setColor(c)}
                className={`w-8 h-8 rounded-lg transition-all ${
                  color === c ? 'ring-2 ring-offset-2 ring-offset-surface-900 ring-white scale-110' : ''
                }`}
                style={{ backgroundColor: c }}
              />
            ))}
          </div>
        </div>
        
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading || !name.trim()}>
            {loading ? 'Creating...' : 'Create'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
