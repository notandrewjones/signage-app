import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, Save, Trash2, Plus, Clock, Calendar, 
  Play, Pause, Image, Video, GripVertical, Eye, EyeOff,
  Maximize, Square, RectangleHorizontal, Sparkles, ChevronDown
} from 'lucide-react';
import { 
  useScheduleGroup, updateScheduleGroup, deleteScheduleGroup,
  createSchedule, updateSchedule, deleteSchedule,
  uploadContent, updateContentItem, deleteContentItem, reorderContent
} from '../hooks/useApi';
import { 
  PageHeader, LoadingState, EmptyState, ConfirmDialog, 
  Toast, Modal, ColorDot, Badge, UploadZone
} from '../components/ui';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const SCALE_MODES = [
  { value: 'fit', label: 'Scale to Fit', icon: RectangleHorizontal, description: 'Fit within frame, may show background' },
  { value: 'fill', label: 'Scale to Fill', icon: Maximize, description: 'Fill frame, may crop edges' },
  { value: 'stretch', label: 'Stretch to Fill', icon: Square, description: 'Stretch to fill, may distort' },
  { value: 'blur', label: 'Fit with Blur', icon: Sparkles, description: 'Fit with blurred background' },
];

function ScheduleForm({ schedule, onSave, onCancel }) {
  const [name, setName] = useState(schedule?.name || '');
  const [startTime, setStartTime] = useState(schedule?.start_time || '09:00');
  const [endTime, setEndTime] = useState(schedule?.end_time || '17:00');
  const [days, setDays] = useState(schedule?.days_of_week || '0123456');
  const [priority, setPriority] = useState(schedule?.priority || 0);
  const [isActive, setIsActive] = useState(schedule?.is_active ?? true);
  
  const toggleDay = (dayIndex) => {
    const idx = dayIndex.toString();
    if (days.includes(idx)) {
      setDays(days.replace(idx, ''));
    } else {
      const newDays = (days + idx).split('').sort().join('');
      setDays(newDays);
    }
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      name,
      start_time: startTime,
      end_time: endTime,
      days_of_week: days,
      priority,
      is_active: isActive,
    });
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-surface-300 mb-2">Schedule Name *</label>
        <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="e.g., Business Hours" className="input" required />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">Start Time</label>
          <input type="time" value={startTime} onChange={e => setStartTime(e.target.value)} className="input" />
        </div>
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">End Time</label>
          <input type="time" value={endTime} onChange={e => setEndTime(e.target.value)} className="input" />
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-surface-300 mb-2">Days of Week</label>
        <div className="flex gap-2">
          {DAYS.map((day, idx) => (
            <button key={day} type="button" onClick={() => toggleDay(idx)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                days.includes(idx.toString())
                  ? 'bg-accent text-white'
                  : 'bg-surface-800 text-surface-400 hover:bg-surface-700'
              }`}
            >
              {day}
            </button>
          ))}
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-surface-300 mb-2">Priority</label>
        <input type="number" value={priority} onChange={e => setPriority(parseInt(e.target.value))} min="0" max="100" className="input w-24" />
        <p className="text-xs text-surface-500 mt-1">Higher priority schedules take precedence</p>
      </div>
      
      <div className="flex items-center gap-3">
        <input type="checkbox" id="scheduleActive" checked={isActive} onChange={e => setIsActive(e.target.checked)} />
        <label htmlFor="scheduleActive" className="text-sm">Schedule is active</label>
      </div>
      
      <div className="flex justify-end gap-3 pt-4 border-t border-surface-800">
        <button type="button" onClick={onCancel} className="btn btn-secondary">Cancel</button>
        <button type="submit" className="btn btn-primary">
          {schedule ? 'Update Schedule' : 'Create Schedule'}
        </button>
      </div>
    </form>
  );
}

function ContentItemCard({ item, onUpdate, onToggle, onDelete, onDragStart, onDragOver, onDrop, isDragging }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [duration, setDuration] = useState(item.display_duration || 10);
  const [scaleMode, setScaleMode] = useState(item.scale_mode || 'fit');
  const [saving, setSaving] = useState(false);
  
  const isVideo = item.file_type === 'video';
  const currentScaleMode = SCALE_MODES.find(m => m.value === (item.scale_mode || 'fit'));
  
  const handleSaveSettings = async () => {
    setSaving(true);
    await onUpdate(item.id, { 
      display_duration: duration,
      scale_mode: scaleMode 
    });
    setSaving(false);
    setIsExpanded(false);
  };
  
  const handleDurationChange = (e) => {
    const value = parseFloat(e.target.value);
    if (!isNaN(value) && value > 0) {
      setDuration(value);
    }
  };
  
  return (
    <div 
      draggable
      onDragStart={(e) => onDragStart(e, item)}
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, item)}
      className={`bg-surface-800 rounded-xl transition-all ${
        isDragging ? 'opacity-50' : ''
      } ${!item.is_active ? 'opacity-60' : ''}`}
    >
      {/* Main Row */}
      <div className="flex items-center gap-4 p-4">
        <div className="cursor-grab active:cursor-grabbing text-surface-500 hover:text-surface-300">
          <GripVertical className="w-5 h-5" />
        </div>
        
        <div className="w-24 h-16 bg-surface-900 rounded-lg overflow-hidden flex-shrink-0">
          {isVideo ? (
            <video src={item.url} className="w-full h-full object-cover" muted />
          ) : (
            <img src={item.url} alt={item.name} className="w-full h-full object-cover" />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {isVideo ? (
              <Video className="w-4 h-4 text-purple-400" />
            ) : (
              <Image className="w-4 h-4 text-blue-400" />
            )}
            <span className="font-medium truncate">{item.name}</span>
            {!item.is_active && <Badge color="gray">Hidden</Badge>}
          </div>
          <div className="flex items-center gap-3 text-sm text-surface-500 mt-1">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {item.display_duration}s
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              {currentScaleMode && <currentScaleMode.icon className="w-3 h-3" />}
              {currentScaleMode?.label || 'Scale to Fit'}
            </span>
            <span>•</span>
            <span>{(item.file_size / 1024 / 1024).toFixed(1)} MB</span>
          </div>
        </div>
        
        <div className="flex items-center gap-1">
          <button 
            onClick={() => setIsExpanded(!isExpanded)} 
            className={`btn btn-ghost p-2 rounded-lg transition-colors ${isExpanded ? 'bg-surface-700' : ''}`}
            title="Edit settings"
          >
            <ChevronDown className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
          </button>
          <button 
            onClick={() => onToggle(item)} 
            className="btn btn-ghost p-2 rounded-lg" 
            title={item.is_active ? 'Hide' : 'Show'}
          >
            {item.is_active ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
          <button 
            onClick={() => onDelete(item)} 
            className="btn btn-ghost p-2 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-500/10"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Expanded Settings Panel */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-2 border-t border-surface-700 ml-9">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Duration */}
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">
                Display Duration (seconds)
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={duration}
                  onChange={handleDurationChange}
                  min="1"
                  max="3600"
                  step="1"
                  className="input w-24"
                />
                <span className="text-sm text-surface-500">seconds</span>
              </div>
              {isVideo && item.duration && (
                <p className="text-xs text-surface-500 mt-1">
                  Video length: {Math.round(item.duration)}s
                  <button 
                    onClick={() => setDuration(Math.round(item.duration))}
                    className="text-accent hover:text-accent-400 ml-2"
                  >
                    Use video length
                  </button>
                </p>
              )}
            </div>
            
            {/* Scale Mode */}
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">
                Scale Mode
              </label>
              <div className="grid grid-cols-2 gap-2">
                {SCALE_MODES.map(mode => (
                  <button
                    key={mode.value}
                    onClick={() => setScaleMode(mode.value)}
                    className={`flex items-center gap-2 p-2 rounded-lg text-left text-sm transition-colors ${
                      scaleMode === mode.value
                        ? 'bg-accent text-white'
                        : 'bg-surface-700 text-surface-300 hover:bg-surface-600'
                    }`}
                    title={mode.description}
                  >
                    <mode.icon className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate">{mode.label}</span>
                  </button>
                ))}
              </div>
              <p className="text-xs text-surface-500 mt-2">
                {SCALE_MODES.find(m => m.value === scaleMode)?.description}
              </p>
            </div>
          </div>
          
          <div className="flex justify-end gap-2 mt-4">
            <button 
              onClick={() => setIsExpanded(false)} 
              className="btn btn-secondary btn-sm"
            >
              Cancel
            </button>
            <button 
              onClick={handleSaveSettings} 
              className="btn btn-primary btn-sm"
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ScheduleGroupDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: group, loading, refetch } = useScheduleGroup(id);
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [color, setColor] = useState('#3B82F6');
  const [isActive, setIsActive] = useState(true);
  const [transitionType, setTransitionType] = useState('cut');
  const [transitionDuration, setTransitionDuration] = useState(0.5);
  
  const [activeTab, setActiveTab] = useState('content');
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deleteGroupConfirm, setDeleteGroupConfirm] = useState(false);
  const [deleteScheduleConfirm, setDeleteScheduleConfirm] = useState(null);
  const [deleteItemConfirm, setDeleteItemConfirm] = useState(null);
  const [showCreateSchedule, setShowCreateSchedule] = useState(false);
  const [editSchedule, setEditSchedule] = useState(null);
  const [toast, setToast] = useState(null);
  const [initialized, setInitialized] = useState(false);
  const [draggedItem, setDraggedItem] = useState(null);
  
  const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];
  
  React.useEffect(() => {
    if (group && !initialized) {
      setName(group.name);
      setDescription(group.description || '');
      setColor(group.color);
      setIsActive(group.is_active);
      setTransitionType(group.transition_type || 'cut');
      setTransitionDuration(group.transition_duration || 0.5);
      setInitialized(true);
    }
  }, [group, initialized]);
  
  const handleSaveGroup = async () => {
    setSaving(true);
    try {
      await updateScheduleGroup(id, { 
        name, 
        description, 
        color, 
        is_active: isActive,
        transition_type: transitionType,
        transition_duration: transitionDuration,
      });
      setToast({ message: 'Schedule group updated', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    } finally {
      setSaving(false);
    }
  };
  
  const handleDeleteGroup = async () => {
    try {
      await deleteScheduleGroup(id);
      navigate('/schedules');
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleCreateSchedule = async (data) => {
    try {
      await createSchedule({ ...data, schedule_group_id: parseInt(id) });
      setShowCreateSchedule(false);
      setToast({ message: 'Schedule created', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleUpdateSchedule = async (scheduleId, data) => {
    try {
      await updateSchedule(scheduleId, data);
      setEditSchedule(null);
      setToast({ message: 'Schedule updated', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleDeleteSchedule = async (scheduleId) => {
    try {
      await deleteSchedule(scheduleId);
      setDeleteScheduleConfirm(null);
      setToast({ message: 'Schedule deleted', type: 'success' });
      refetch();
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
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleToggleItemActive = async (item) => {
    try {
      await updateContentItem(item.id, { is_active: !item.is_active });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleDeleteItem = async (itemId) => {
    try {
      await deleteContentItem(itemId);
      setDeleteItemConfirm(null);
      setToast({ message: 'Content deleted', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
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
    
    const items = [...(group.content_items || [])];
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
    return <LoadingState message="Loading schedule group..." />;
  }
  
  const contentItems = group.content_items || [];
  const schedules = group.schedules || [];
  
  return (
    <div>
      <div className="mb-6">
        <Link to="/schedules" className="inline-flex items-center gap-2 text-surface-400 hover:text-surface-200 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back to Schedules
        </Link>
      </div>
      
      <PageHeader 
        title={
          <div className="flex items-center gap-3">
            <ColorDot color={group.color} size="lg" />
            {group.name}
          </div>
        }
        description={group.description}
        actions={
          <div className="flex items-center gap-3">
            <button onClick={() => setDeleteGroupConfirm(true)} className="btn btn-danger">
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
            <button onClick={handleSaveGroup} className="btn btn-primary" disabled={saving}>
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        }
      />
      
      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-surface-800 rounded-xl mb-6 w-fit">
        <button
          onClick={() => setActiveTab('content')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'content' ? 'bg-accent text-white' : 'text-surface-400 hover:text-white'
          }`}
        >
          Content ({contentItems.length})
        </button>
        <button
          onClick={() => setActiveTab('schedules')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'schedules' ? 'bg-accent text-white' : 'text-surface-400 hover:text-white'
          }`}
        >
          Schedules ({schedules.length})
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'settings' ? 'bg-accent text-white' : 'text-surface-400 hover:text-white'
          }`}
        >
          Settings
        </button>
      </div>
      
      {/* Content Tab */}
      {activeTab === 'content' && (
        <div className="space-y-6">
          <UploadZone onFilesSelected={handleFilesSelected} uploading={uploading} accept="image/*,video/*" />
          
          {contentItems.length === 0 ? (
            <EmptyState icon={Image} title="No content yet" description="Upload images or videos to display in this schedule group" />
          ) : (
            <div className="space-y-3">
              {contentItems.map(item => (
                <ContentItemCard
                  key={item.id}
                  item={item}
                  onUpdate={handleUpdateItem}
                  onToggle={handleToggleItemActive}
                  onDelete={() => setDeleteItemConfirm(item)}
                  onDragStart={handleDragStart}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                  isDragging={draggedItem?.id === item.id}
                />
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Schedules Tab */}
      {activeTab === 'schedules' && (
        <div className="space-y-6">
          <div className="flex justify-end">
            <button onClick={() => setShowCreateSchedule(true)} className="btn btn-primary">
              <Plus className="w-4 h-4" />
              Add Schedule
            </button>
          </div>
          
          {schedules.length === 0 ? (
            <EmptyState icon={Calendar} title="No schedules" description="Add a schedule to control when this content plays" />
          ) : (
            <div className="space-y-3">
              {schedules.map(schedule => (
                <div key={schedule.id} className="card p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`p-2 rounded-lg ${schedule.is_active ? 'bg-green-500/20' : 'bg-surface-800'}`}>
                        {schedule.is_active ? (
                          <Play className="w-5 h-5 text-green-400" />
                        ) : (
                          <Pause className="w-5 h-5 text-surface-500" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{schedule.name}</span>
                          {!schedule.is_active && <Badge color="gray">Inactive</Badge>}
                        </div>
                        <div className="flex items-center gap-4 mt-1 text-sm text-surface-400">
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {schedule.start_time} - {schedule.end_time}
                          </div>
                          <div className="flex gap-1">
                            {DAYS.map((day, idx) => (
                              <span key={day} className={`text-xs ${
                                schedule.days_of_week.includes(idx.toString()) 
                                  ? 'text-accent' 
                                  : 'text-surface-600'
                              }`}>
                                {day[0]}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={() => setEditSchedule(schedule)} className="btn btn-secondary btn-sm">
                        Edit
                      </button>
                      <button onClick={() => setDeleteScheduleConfirm(schedule)} className="btn btn-icon btn-ghost text-red-400">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="card p-6 max-w-2xl">
          <h2 className="section-title">Group Settings</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">Name *</label>
              <input type="text" value={name} onChange={e => setName(e.target.value)} className="input" />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">Description</label>
              <textarea value={description} onChange={e => setDescription(e.target.value)} className="input min-h-[80px]" placeholder="Optional description" />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">Color</label>
              <div className="flex gap-2">
                {colors.map(c => (
                  <button key={c} onClick={() => setColor(c)}
                    className={`w-8 h-8 rounded-full transition-transform ${color === c ? 'ring-2 ring-white ring-offset-2 ring-offset-surface-900 scale-110' : ''}`}
                    style={{ backgroundColor: c }}
                  />
                ))}
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <input type="checkbox" id="groupActive" checked={isActive} onChange={e => setIsActive(e.target.checked)} />
              <label htmlFor="groupActive" className="text-sm">Group is active</label>
            </div>
            
            {/* Transition Settings */}
            <div className="pt-4 border-t border-surface-800">
              <h3 className="font-medium mb-4">Transition Settings</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-surface-300 mb-2">Transition Type</label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setTransitionType('cut')}
                      className={`flex-1 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                        transitionType === 'cut'
                          ? 'bg-accent text-white'
                          : 'bg-surface-800 text-surface-400 hover:bg-surface-700'
                      }`}
                    >
                      Hard Cut
                    </button>
                    <button
                      onClick={() => setTransitionType('dissolve')}
                      className={`flex-1 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                        transitionType === 'dissolve'
                          ? 'bg-accent text-white'
                          : 'bg-surface-800 text-surface-400 hover:bg-surface-700'
                      }`}
                    >
                      Dissolve
                    </button>
                  </div>
                </div>
                
                {transitionType === 'dissolve' && (
                  <div>
                    <label className="block text-sm font-medium text-surface-300 mb-2">
                      Transition Duration: {transitionDuration.toFixed(1)}s
                    </label>
                    <input
                      type="range"
                      min="0.1"
                      max="3"
                      step="0.1"
                      value={transitionDuration}
                      onChange={e => setTransitionDuration(parseFloat(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-surface-500 mt-1">
                      <span>0.1s</span>
                      <span>1.5s</span>
                      <span>3s</span>
                    </div>
                  </div>
                )}
                
                <p className="text-sm text-surface-500">
                  {transitionType === 'cut' 
                    ? 'Content will switch instantly with no transition effect.'
                    : `Content will crossfade over ${transitionDuration.toFixed(1)} seconds.`
                  }
                </p>
              </div>
            </div>
            
            <div className="pt-4 border-t border-surface-800">
              <h3 className="font-medium mb-2">Assigned Devices</h3>
              {group.devices?.length === 0 ? (
                <p className="text-sm text-surface-500">No devices assigned to this group</p>
              ) : (
                <div className="space-y-2">
                  {group.devices?.map(device => (
                    <Link key={device.id} to={`/devices/${device.id}`} className="block p-3 bg-surface-800 rounded-lg hover:bg-surface-700 transition-colors">
                      <span className="font-medium">{device.name}</span>
                      {device.location && <span className="text-surface-500 ml-2">• {device.location}</span>}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Modals */}
      <Modal isOpen={showCreateSchedule} onClose={() => setShowCreateSchedule(false)} title="Create Schedule">
        <ScheduleForm onSave={handleCreateSchedule} onCancel={() => setShowCreateSchedule(false)} />
      </Modal>
      
      <Modal isOpen={!!editSchedule} onClose={() => setEditSchedule(null)} title="Edit Schedule">
        {editSchedule && (
          <ScheduleForm schedule={editSchedule} onSave={(data) => handleUpdateSchedule(editSchedule.id, data)} onCancel={() => setEditSchedule(null)} />
        )}
      </Modal>
      
      <ConfirmDialog isOpen={deleteGroupConfirm} onClose={() => setDeleteGroupConfirm(false)} onConfirm={handleDeleteGroup} title="Delete Schedule Group" message="This will permanently delete this group and all its content. This cannot be undone." confirmText="Delete" danger />
      
      <ConfirmDialog isOpen={!!deleteScheduleConfirm} onClose={() => setDeleteScheduleConfirm(null)} onConfirm={() => handleDeleteSchedule(deleteScheduleConfirm?.id)} title="Delete Schedule" message="Are you sure you want to delete this schedule?" confirmText="Delete" danger />
      
      <ConfirmDialog isOpen={!!deleteItemConfirm} onClose={() => setDeleteItemConfirm(null)} onConfirm={() => handleDeleteItem(deleteItemConfirm?.id)} title="Delete Content" message="Are you sure you want to delete this content item?" confirmText="Delete" danger />
      
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}