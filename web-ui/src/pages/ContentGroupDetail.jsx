import React, { useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, Save, Trash2, Plus, Upload, Image, Video, 
  Play, Pause, Clock, GripVertical, MoreVertical, Eye, EyeOff
} from 'lucide-react';
import { 
  useContentGroup, updateContentGroup, deleteContentGroup,
  uploadContent, updateContentItem, deleteContentItem, reorderContent
} from '../hooks/useApi';
import { 
  PageHeader, LoadingState, EmptyState, ConfirmDialog, 
  Toast, UploadZone, Modal, ColorDot, Badge 
} from '../components/ui';

export default function ContentGroupDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: group, loading, refetch } = useContentGroup(id);
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [color, setColor] = useState('#3B82F6');
  
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deleteGroupConfirm, setDeleteGroupConfirm] = useState(false);
  const [deleteItemConfirm, setDeleteItemConfirm] = useState(null);
  const [editItem, setEditItem] = useState(null);
  const [toast, setToast] = useState(null);
  const [initialized, setInitialized] = useState(false);
  const [draggedItem, setDraggedItem] = useState(null);
  
  const colors = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', 
    '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'
  ];
  
  // Initialize form
  React.useEffect(() => {
    if (group && !initialized) {
      setName(group.name);
      setDescription(group.description || '');
      setColor(group.color);
      setInitialized(true);
    }
  }, [group, initialized]);
  
  const handleSaveGroup = async () => {
    setSaving(true);
    try {
      await updateContentGroup(id, { name, description, color });
      setToast({ message: 'Group updated', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    } finally {
      setSaving(false);
    }
  };
  
  const handleDeleteGroup = async () => {
    try {
      await deleteContentGroup(id);
      navigate('/content');
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleFilesSelected = async (files) => {
    setUploading(true);
    try {
      for (const file of files) {
        await uploadContent(id, file, file.name);
      }
      setToast({ message: `${files.length} file(s) uploaded`, type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    } finally {
      setUploading(false);
    }
  };
  
  const handleUpdateItem = async (itemId, data) => {
    try {
      await updateContentItem(itemId, data);
      setEditItem(null);
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleDeleteItem = async (itemId) => {
    try {
      await deleteContentItem(itemId);
      setToast({ message: 'Content deleted', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleToggleActive = async (item) => {
    await handleUpdateItem(item.id, { is_active: !item.is_active });
  };
  
  // Drag and drop reordering
  const handleDragStart = (e, item) => {
    setDraggedItem(item);
    e.dataTransfer.effectAllowed = 'move';
  };
  
  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };
  
  const handleDrop = async (e, targetItem) => {
    e.preventDefault();
    if (!draggedItem || draggedItem.id === targetItem.id) return;
    
    const items = [...group.content_items];
    const dragIndex = items.findIndex(i => i.id === draggedItem.id);
    const targetIndex = items.findIndex(i => i.id === targetItem.id);
    
    items.splice(dragIndex, 1);
    items.splice(targetIndex, 0, draggedItem);
    
    const newOrder = items.map(i => i.id);
    
    try {
      await reorderContent(id, newOrder);
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
    
    setDraggedItem(null);
  };
  
  if (loading || !group) {
    return <LoadingState message="Loading content group..." />;
  }
  
  return (
    <div>
      <div className="mb-6">
        <Link to="/content" className="inline-flex items-center gap-2 text-surface-400 hover:text-surface-200 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back to Content
        </Link>
      </div>
      
      <PageHeader 
        title={
          <div className="flex items-center gap-3">
            <ColorDot color={group.color} size="lg" />
            <span>{group.name}</span>
          </div>
        }
        actions={
          <div className="flex items-center gap-3">
            <button onClick={() => setDeleteGroupConfirm(true)} className="btn btn-danger">
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
            <button onClick={handleSaveGroup} className="btn btn-primary" disabled={saving}>
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        }
      />
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings */}
        <div className="card p-6">
          <h2 className="section-title">Group Settings</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">
                Name *
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
                Description
              </label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="input min-h-[80px]"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">
                Color
              </label>
              <div className="flex flex-wrap gap-2">
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
          </div>
        </div>
        
        {/* Content */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="px-6 py-4 border-b border-surface-800">
              <h2 className="font-semibold">Content Items</h2>
            </div>
            
            <div className="p-6">
              <UploadZone 
                onFilesSelected={handleFilesSelected}
                accept="image/*,video/*"
              >
                <Upload className="w-10 h-10 text-surface-500 mx-auto mb-3" />
                <p className="text-surface-300 font-medium">
                  {uploading ? 'Uploading...' : 'Drop files here or click to upload'}
                </p>
                <p className="text-sm text-surface-500 mt-1">
                  Supports images and videos
                </p>
              </UploadZone>
            </div>
            
            {group.content_items?.length === 0 ? (
              <div className="p-6 pt-0">
                <EmptyState
                  icon={Image}
                  title="No content yet"
                  description="Upload images or videos to this group"
                />
              </div>
            ) : (
              <div className="divide-y divide-surface-800">
                {group.content_items.map((item, index) => (
                  <ContentItemRow
                    key={item.id}
                    item={item}
                    index={index}
                    onEdit={() => setEditItem(item)}
                    onDelete={() => setDeleteItemConfirm(item)}
                    onToggleActive={() => handleToggleActive(item)}
                    onDragStart={handleDragStart}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    isDragging={draggedItem?.id === item.id}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      
      <ConfirmDialog
        isOpen={deleteGroupConfirm}
        onClose={() => setDeleteGroupConfirm(false)}
        onConfirm={handleDeleteGroup}
        title="Delete Content Group"
        message="Are you sure? All content in this group will be permanently deleted."
        confirmText="Delete"
        danger
      />
      
      <ConfirmDialog
        isOpen={!!deleteItemConfirm}
        onClose={() => setDeleteItemConfirm(null)}
        onConfirm={() => handleDeleteItem(deleteItemConfirm.id)}
        title="Delete Content"
        message={`Delete "${deleteItemConfirm?.name}"?`}
        confirmText="Delete"
        danger
      />
      
      {editItem && (
        <EditItemModal
          item={editItem}
          onClose={() => setEditItem(null)}
          onSave={(data) => handleUpdateItem(editItem.id, data)}
        />
      )}
      
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

function ContentItemRow({ item, index, onEdit, onDelete, onToggleActive, onDragStart, onDragOver, onDrop, isDragging }) {
  const [showMenu, setShowMenu] = useState(false);
  const isVideo = item.file_type === 'video';
  
  return (
    <div 
      className={`flex items-center gap-4 px-6 py-4 hover:bg-surface-800/50 transition-colors ${
        isDragging ? 'opacity-50' : ''
      } ${!item.is_active ? 'opacity-60' : ''}`}
      draggable
      onDragStart={e => onDragStart(e, item)}
      onDragOver={onDragOver}
      onDrop={e => onDrop(e, item)}
    >
      <div className="cursor-grab text-surface-500 hover:text-surface-300">
        <GripVertical className="w-5 h-5" />
      </div>
      
      <div className="w-16 h-16 bg-surface-800 rounded-lg overflow-hidden flex-shrink-0">
        {isVideo ? (
          <div className="w-full h-full flex items-center justify-center">
            <Video className="w-6 h-6 text-surface-400" />
          </div>
        ) : (
          <img 
            src={item.url} 
            alt={item.name}
            className="w-full h-full object-cover"
          />
        )}
      </div>
      
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{item.name}</p>
        <div className="flex items-center gap-3 text-sm text-surface-500">
          <span className="flex items-center gap-1">
            {isVideo ? <Video className="w-3 h-3" /> : <Image className="w-3 h-3" />}
            {item.file_type}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {item.display_duration}s
          </span>
          <span>{(item.file_size / 1024 / 1024).toFixed(1)} MB</span>
        </div>
      </div>
      
      {!item.is_active && (
        <Badge color="gray">Hidden</Badge>
      )}
      
      <div className="relative">
        <button 
          onClick={() => setShowMenu(!showMenu)}
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
              <button 
                onClick={() => { setShowMenu(false); onEdit(); }}
                className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-surface-700 transition-colors w-full"
              >
                <Clock className="w-4 h-4" />
                Edit Duration
              </button>
              <button 
                onClick={() => { setShowMenu(false); onToggleActive(); }}
                className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-surface-700 transition-colors w-full"
              >
                {item.is_active ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                {item.is_active ? 'Hide' : 'Show'}
              </button>
              <button 
                onClick={() => { setShowMenu(false); onDelete(); }}
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

function EditItemModal({ item, onClose, onSave }) {
  const [name, setName] = useState(item.name);
  const [displayDuration, setDisplayDuration] = useState(item.display_duration);
  const [saving, setSaving] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    await onSave({ name, display_duration: displayDuration });
    setSaving(false);
  };
  
  return (
    <Modal isOpen={true} onClose={onClose} title="Edit Content">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">
            Name
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
            Display Duration (seconds)
          </label>
          <input
            type="number"
            value={displayDuration}
            onChange={e => setDisplayDuration(parseFloat(e.target.value))}
            min="1"
            step="1"
            className="input"
          />
          <p className="text-xs text-surface-500 mt-1">
            How long to display this item before moving to the next
          </p>
        </div>
        
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
