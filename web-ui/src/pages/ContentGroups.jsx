import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, FolderOpen, MoreVertical, Trash2, Edit, Image, Video, FileText } from 'lucide-react';
import { useContentGroups, createContentGroup, deleteContentGroup } from '../hooks/useApi';
import { PageHeader, LoadingState, EmptyState, Modal, ConfirmDialog, Toast, ColorDot } from '../components/ui';

export default function ContentGroups() {
  const { data: groups, loading, refetch } = useContentGroups();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [toast, setToast] = useState(null);
  const navigate = useNavigate();
  
  const handleCreate = async (data) => {
    try {
      const group = await createContentGroup(data);
      setShowCreateModal(false);
      setToast({ message: 'Content group created', type: 'success' });
      refetch();
      navigate(`/content/${group.id}`);
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleDelete = async (id) => {
    try {
      await deleteContentGroup(id);
      setToast({ message: 'Content group deleted', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  if (loading) {
    return <LoadingState message="Loading content groups..." />;
  }
  
  return (
    <div>
      <PageHeader 
        title="Content" 
        description="Organize your media into groups"
        actions={
          <button 
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            <Plus className="w-5 h-5" />
            New Group
          </button>
        }
      />
      
      {groups?.length === 0 ? (
        <EmptyState
          icon={FolderOpen}
          title="No content groups"
          description="Create your first content group to start organizing media"
          action={
            <button 
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary"
            >
              <Plus className="w-5 h-5" />
              New Group
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups.map(group => (
            <ContentGroupCard 
              key={group.id} 
              group={group} 
              onDelete={() => setDeleteConfirm(group)}
            />
          ))}
        </div>
      )}
      
      <CreateGroupModal 
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreate}
      />
      
      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => handleDelete(deleteConfirm.id)}
        title="Delete Content Group"
        message={`Are you sure you want to delete "${deleteConfirm?.name}"? All content in this group will be deleted.`}
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

function ContentGroupCard({ group, onDelete }) {
  const [showMenu, setShowMenu] = useState(false);
  
  return (
    <div className="card-hover relative">
      <Link to={`/content/${group.id}`} className="block p-5">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div 
              className="p-3 rounded-xl"
              style={{ backgroundColor: `${group.color}20` }}
            >
              <FolderOpen className="w-6 h-6" style={{ color: group.color }} />
            </div>
            <div>
              <h3 className="font-semibold">{group.name}</h3>
              <p className="text-sm text-surface-500">
                {group.content_count} item{group.content_count !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <ColorDot color={group.color} size="md" />
        </div>
        
        {group.description && (
          <p className="text-sm text-surface-400 line-clamp-2">
            {group.description}
          </p>
        )}
      </Link>
      
      <div className="absolute top-4 right-12">
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
                to={`/content/${group.id}`}
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

function CreateGroupModal({ isOpen, onClose, onCreate }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [color, setColor] = useState('#3B82F6');
  const [loading, setLoading] = useState(false);
  
  const colors = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', 
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
    setColor('#3B82F6');
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Content Group">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">
            Group Name *
          </label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g., Gym Promotions"
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
            <input
              type="color"
              value={color}
              onChange={e => setColor(e.target.value)}
              className="w-8 h-8"
            />
          </div>
        </div>
        
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading || !name.trim()}>
            {loading ? 'Creating...' : 'Create Group'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
