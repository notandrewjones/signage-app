import React, { useState, useRef, useEffect } from 'react';
import { X, AlertCircle, Check, Loader2, ChevronDown } from 'lucide-react';

// Modal Component
export function Modal({ isOpen, onClose, title, children, size = 'md' }) {
  if (!isOpen) return null;
  
  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };
  
  return (
    <div className="modal-backdrop flex items-center justify-center p-4" onClick={onClose}>
      <div 
        className={`card ${sizeClasses[size]} w-full animate-in`}
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-800">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button 
            onClick={onClose}
            className="btn-ghost p-2 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
}

// Confirm Dialog
export function ConfirmDialog({ isOpen, onClose, onConfirm, title, message, confirmText = 'Confirm', danger = false }) {
  if (!isOpen) return null;
  
  return (
    <div className="modal-backdrop flex items-center justify-center p-4" onClick={onClose}>
      <div 
        className="card max-w-md w-full animate-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="p-6">
          <div className="flex items-start gap-4">
            <div className={`p-2 rounded-full ${danger ? 'bg-red-500/10' : 'bg-amber-500/10'}`}>
              <AlertCircle className={`w-6 h-6 ${danger ? 'text-red-400' : 'text-amber-400'}`} />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold mb-2">{title}</h3>
              <p className="text-surface-400">{message}</p>
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <button onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button 
              onClick={() => { onConfirm(); onClose(); }}
              className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Toast Notifications
export function Toast({ message, type = 'info', onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);
  
  const icons = {
    success: <Check className="w-5 h-5 text-green-400" />,
    error: <AlertCircle className="w-5 h-5 text-red-400" />,
    info: <AlertCircle className="w-5 h-5 text-blue-400" />,
  };
  
  const bgColors = {
    success: 'bg-green-500/10 border-green-500/20',
    error: 'bg-red-500/10 border-red-500/20',
    info: 'bg-blue-500/10 border-blue-500/20',
  };
  
  return (
    <div className={`fixed bottom-4 right-4 flex items-center gap-3 px-4 py-3 rounded-lg border ${bgColors[type]} animate-in z-50`}>
      {icons[type]}
      <span className="text-sm">{message}</span>
      <button onClick={onClose} className="text-surface-400 hover:text-surface-200">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

// Loading Spinner
export function Spinner({ size = 'md', className = '' }) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };
  
  return (
    <Loader2 className={`animate-spin ${sizes[size]} ${className}`} />
  );
}

// Loading State
export function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Spinner size="lg" className="text-accent mb-4" />
      <p className="text-surface-400">{message}</p>
    </div>
  );
}

// Empty State
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="p-4 bg-surface-800 rounded-full mb-4">
        <Icon className="w-8 h-8 text-surface-400" />
      </div>
      <h3 className="text-lg font-medium mb-2">{title}</h3>
      <p className="text-surface-400 mb-6 max-w-md">{description}</p>
      {action}
    </div>
  );
}

// File Upload Zone
export function UploadZone({ onFilesSelected, accept, multiple = true, children }) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);
  
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };
  
  const handleDragIn = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  
  const handleDragOut = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onFilesSelected(multiple ? files : [files[0]]);
    }
  };
  
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      onFilesSelected(multiple ? files : [files[0]]);
    }
    e.target.value = '';
  };
  
  return (
    <div
      className={`upload-zone ${isDragging ? 'drag-over' : ''}`}
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileSelect}
        className="hidden"
      />
      {children}
    </div>
  );
}

// Badge
export function Badge({ children, color = 'gray', className = '' }) {
  const colors = {
    gray: 'bg-surface-700 text-surface-300',
    green: 'bg-green-500/10 text-green-400 border border-green-500/20',
    red: 'bg-red-500/10 text-red-400 border border-red-500/20',
    blue: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
    yellow: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border border-purple-500/20',
  };
  
  return (
    <span className={`badge ${colors[color]} ${className}`}>
      {children}
    </span>
  );
}

// Tabs
export function Tabs({ tabs, activeTab, onChange }) {
  return (
    <div className="flex gap-1 p-1 bg-surface-800 rounded-lg">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
            activeTab === tab.id
              ? 'bg-surface-700 text-white'
              : 'text-surface-400 hover:text-white hover:bg-surface-700/50'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

// Select Dropdown
export function Select({ value, onChange, options, placeholder = 'Select...', className = '' }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className={`select pr-10 ${className}`}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400 pointer-events-none" />
    </div>
  );
}

// Color Dot
export function ColorDot({ color, size = 'md' }) {
  const sizes = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  };
  
  return (
    <span 
      className={`${sizes[size]} rounded-full inline-block`}
      style={{ backgroundColor: color }}
    />
  );
}

// Status Indicator
export function StatusIndicator({ online }) {
  return (
    <span className={`status-dot ${online ? 'status-online' : 'status-offline'}`} />
  );
}

// Page Header
export function PageHeader({ title, description, actions }) {
  return (
    <div className="flex items-center justify-between mb-8">
      <div>
        <h1 className="text-2xl font-bold mb-1">{title}</h1>
        {description && <p className="text-surface-400">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  );
}

// Stat Card
export function StatCard({ icon: Icon, label, value, color = 'accent' }) {
  const colorClasses = {
    accent: 'text-accent bg-accent/10',
    green: 'text-green-400 bg-green-500/10',
    blue: 'text-blue-400 bg-blue-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
  };
  
  return (
    <div className="card p-5">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-xl ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-sm text-surface-400">{label}</p>
        </div>
      </div>
    </div>
  );
}
