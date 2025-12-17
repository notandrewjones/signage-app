import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, Save, Trash2, Plus, Clock, Calendar, 
  MoreVertical, Play, Pause, FolderOpen
} from 'lucide-react';
import { 
  useScheduleGroup, useContentGroups, updateScheduleGroup, deleteScheduleGroup,
  createSchedule, updateSchedule, deleteSchedule
} from '../hooks/useApi';
import { 
  PageHeader, LoadingState, EmptyState, ConfirmDialog, 
  Toast, Modal, ColorDot, Badge
} from '../components/ui';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function ScheduleGroupDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: group, loading, refetch } = useScheduleGroup(id);
  const { data: contentGroups } = useContentGroups();
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [color, setColor] = useState('#10B981');
  const [isActive, setIsActive] = useState(true);
  
  const [saving, setSaving] = useState(false);
  const [deleteGroupConfirm, setDeleteGroupConfirm] = useState(false);
  const [deleteScheduleConfirm, setDeleteScheduleConfirm] = useState(null);
  const [showCreateSchedule, setShowCreateSchedule] = useState(false);
  const [editSchedule, setEditSchedule] = useState(null);
  const [toast, setToast] = useState(null);
  const [initialized, setInitialized] = useState(false);
  
  const colors = [
    '#10B981', '#3B82F6', '#F59E0B', '#EF4444', 
    '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'
  ];
  
  React.useEffect(() => {
    if (group && !initialized) {
      setName(group.name);
      setDescription(group.description || '');
      setColor(group.color);
      setIsActive(group.is_active);
      setInitialized(true);
    }
  }, [group, initialized]);
  
  const handleSaveGroup = async () => {
    setSaving(true);
    try {
      await updateScheduleGroup(id, { name, description, color, is_active: isActive });
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
      setToast({ message: 'Schedule deleted', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  if (loading || !group) {
    return <LoadingState message="Loading schedule group..." />;
  }
  
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
            <span>{group.name}</span>
            {group.is_active ? (
              <Badge color="green">Active</Badge>
            ) : (
              <Badge color="gray">Inactive</Badge>
            )}
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
              <label className="block text-sm font-medium text-surface-300 mb-2">Name *</label>
              <input type="text" value={name} onChange={e => setName(e.target.value)} className="input" />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">Description</label>
              <textarea value={description} onChange={e => setDescription(e.target.value)} className="input min-h-[80px]" />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">Color</label>
              <div className="flex flex-wrap gap-2">
                {colors.map(c => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setColor(c)}
                    className={`w-8 h-8 rounded-lg transition-all ${color === c ? 'ring-2 ring-offset-2 ring-offset-surface-900 ring-white scale-110' : ''}`}
                    style={{ backgroundColor: c }}
                  />
                ))}
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <input type="checkbox" id="isActive" checked={isActive} onChange={e => setIsActive(e.target.checked)} />
              <label htmlFor="isActive" className="text-sm">Schedule group is active</label>
            </div>
          </div>
          
          <div className="mt-8 pt-6 border-t border-surface-800">
            <h3 className="text-sm font-medium text-surface-300 mb-4">Assigned Devices</h3>
            {group.devices?.length === 0 ? (
              <p className="text-sm text-surface-500">No devices assigned</p>
            ) : (
              <div className="space-y-2">
                {group.devices.map(device => (
                  <Link key={device.id} to={`/devices/${device.id}`} className="flex items-center gap-3 p-2 rounded-lg hover:bg-surface-800 transition-colors">
                    <span className={`status-dot ${device.is_online ? 'status-online' : 'status-offline'}`} />
                    <span className="text-sm">{device.name}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* Schedules */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between px-6 py-4 border-b border-surface-800">
              <h2 className="font-semibold">Schedules</h2>
              <button onClick={() => setShowCreateSchedule(true)} className="btn btn-primary">
                <Plus className="w-4 h-4" />
                Add Schedule
              </button>
            </div>
            
            {group.schedules?.length === 0 ? (
              <div className="p-6">
                <EmptyState icon={Clock} title="No schedules" description="Add schedules to define when content plays" />
              </div>
            ) : (
              <div className="divide-y divide-surface-800">
                {group.schedules.map(schedule => (
                  <ScheduleRow
                    key={schedule.id}
                    schedule={schedule}
                    onEdit={() => setEditSchedule(schedule)}
                    onDelete={() => setDeleteScheduleConfirm(schedule)}
                    onToggleActive={() => handleUpdateSchedule(schedule.id, { is_active: !schedule.is_active })}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      
      <ConfirmDialog isOpen={deleteGroupConfirm} onClose={() => setDeleteGroupConfirm(false)} onConfirm={handleDeleteGroup} title="Delete Schedule Group" message="All schedules will be deleted." confirmText="Delete" danger />
      <ConfirmDialog isOpen={!!deleteScheduleConfirm} onClose={() => setDeleteScheduleConfirm(null)} onConfirm={() => handleDeleteSchedule(deleteScheduleConfirm.id)} title="Delete Schedule" message={`Delete "${deleteScheduleConfirm?.name}"?`} confirmText="Delete" danger />
      
      {showCreateSchedule && <ScheduleModal contentGroups={contentGroups || []} onClose={() => setShowCreateSchedule(false)} onSave={handleCreateSchedule} />}
      {editSchedule && <ScheduleModal schedule={editSchedule} contentGroups={contentGroups || []} onClose={() => setEditSchedule(null)} onSave={(data) => handleUpdateSchedule(editSchedule.id, data)} />}
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}

function ScheduleRow({ schedule, onEdit, onDelete, onToggleActive }) {
  const [showMenu, setShowMenu] = useState(false);
  
  return (
    <div className={`px-6 py-4 ${!schedule.is_active ? 'opacity-60' : ''}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <h3 className="font-medium">{schedule.name}</h3>
          {!schedule.is_active && <Badge color="gray">Inactive</Badge>}
          {schedule.priority > 0 && <Badge color="purple">Priority {schedule.priority}</Badge>}
        </div>
        
        <div className="relative">
          <button onClick={() => setShowMenu(!showMenu)} className="btn-ghost p-2 rounded-lg">
            <MoreVertical className="w-4 h-4" />
          </button>
          
          {showMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
              <div className="absolute right-0 top-full mt-1 w-40 bg-surface-800 border border-surface-700 rounded-lg shadow-xl z-20 py-1">
                <button onClick={() => { setShowMenu(false); onEdit(); }} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-surface-700 transition-colors w-full">
                  <Clock className="w-4 h-4" />Edit
                </button>
                <button onClick={() => { setShowMenu(false); onToggleActive(); }} className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-surface-700 transition-colors w-full">
                  {schedule.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  {schedule.is_active ? 'Disable' : 'Enable'}
                </button>
                <button onClick={() => { setShowMenu(false); onDelete(); }} className="flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-surface-700 transition-colors w-full">
                  <Trash2 className="w-4 h-4" />Delete
                </button>
              </div>
            </>
          )}
        </div>
      </div>
      
      <div className="flex items-center gap-6 text-sm text-surface-400 mb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4" />
          <span>{schedule.start_time} - {schedule.end_time}</span>
        </div>
        <div className="flex items-center gap-1">
          {DAYS.map((day, idx) => (
            <span key={day} className={`w-7 h-7 flex items-center justify-center rounded text-xs ${schedule.days_of_week.includes(idx.toString()) ? 'bg-accent/20 text-accent' : 'bg-surface-800 text-surface-600'}`}>
              {day.charAt(0)}
            </span>
          ))}
        </div>
      </div>
      
      {schedule.content_groups?.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <FolderOpen className="w-4 h-4 text-surface-500" />
          {schedule.content_groups.map(group => (
            <span key={group.id} className="inline-flex items-center gap-1.5 px-2 py-1 bg-surface-800 rounded text-xs">
              <ColorDot color={group.color} size="sm" />{group.name}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ScheduleModal({ schedule, contentGroups, onClose, onSave }) {
  const [name, setName] = useState(schedule?.name || '');
  const [startTime, setStartTime] = useState(schedule?.start_time || '09:00');
  const [endTime, setEndTime] = useState(schedule?.end_time || '17:00');
  const [daysOfWeek, setDaysOfWeek] = useState(schedule?.days_of_week || '01234');
  const [priority, setPriority] = useState(schedule?.priority || 0);
  const [selectedGroups, setSelectedGroups] = useState(schedule?.content_groups?.map(g => g.id) || []);
  const [saving, setSaving] = useState(false);
  
  const toggleDay = (idx) => {
    const idxStr = idx.toString();
    if (daysOfWeek.includes(idxStr)) {
      setDaysOfWeek(daysOfWeek.replace(idxStr, ''));
    } else {
      setDaysOfWeek((daysOfWeek + idxStr).split('').sort().join(''));
    }
  };
  
  const toggleGroup = (groupId) => {
    setSelectedGroups(prev => prev.includes(groupId) ? prev.filter(id => id !== groupId) : [...prev, groupId]);
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    await onSave({ name, start_time: startTime, end_time: endTime, days_of_week: daysOfWeek, priority, content_group_ids: selectedGroups });
    setSaving(false);
  };
  
  return (
    <Modal isOpen={true} onClose={onClose} title={schedule ? 'Edit Schedule' : 'Create Schedule'} size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">Schedule Name *</label>
          <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="e.g., Morning Hours" className="input" required />
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
          <label className="block text-sm font-medium text-surface-300 mb-2">Days</label>
          <div className="flex items-center gap-2">
            {DAYS.map((day, idx) => (
              <button key={day} type="button" onClick={() => toggleDay(idx)} className={`w-10 h-10 flex items-center justify-center rounded-lg text-sm font-medium transition-all ${daysOfWeek.includes(idx.toString()) ? 'bg-accent text-white' : 'bg-surface-800 text-surface-400 hover:bg-surface-700'}`}>
                {day}
              </button>
            ))}
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">Priority</label>
          <input type="number" value={priority} onChange={e => setPriority(parseInt(e.target.value) || 0)} min="0" className="input" />
          <p className="text-xs text-surface-500 mt-1">Higher priority schedules take precedence</p>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-surface-300 mb-2">Content Groups</label>
          {contentGroups.length === 0 ? (
            <p className="text-sm text-surface-500">No content groups available</p>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {contentGroups.map(group => (
                <label key={group.id} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${selectedGroups.includes(group.id) ? 'border-accent bg-accent/5' : 'border-surface-700 hover:border-surface-600'}`}>
                  <input type="checkbox" checked={selectedGroups.includes(group.id)} onChange={() => toggleGroup(group.id)} />
                  <ColorDot color={group.color} />
                  <span className="flex-1">{group.name}</span>
                  <span className="text-sm text-surface-400">{group.content_count} items</span>
                </label>
              ))}
            </div>
          )}
        </div>
        
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={saving || !name.trim()}>{saving ? 'Saving...' : schedule ? 'Update' : 'Create'}</button>
        </div>
      </form>
    </Modal>
  );
}
