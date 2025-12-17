import React, { useState, useRef, useEffect } from 'react';
import { X, Upload, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

// Page Header
export function PageHeader({ title, description, actions }) {
  return (
    <div className="flex items-start justify-between mb-8">
      <div>
        <h1 className="text-2xl font-bold mb-1">{title}</h1>
        {description && <p className="text-surface-400">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  );
}

// Loading State
export function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <Loader2 className="w-8 h-8 text-accent animate-spin mb-4" />
      <p className="text-surface-400">{message}</p>
    </div>
  );
}

// Empty State
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && (
        <div className="p-4 bg-surface-800 rounded-2xl mb-4">
          <Icon className="w-8 h-8 text-surface-500" />
        </div>
      )}
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-surface-400 mb-6 max-w-md">{description}</p>
      {action}
    </div>
  );
}

// Stat Card
export function StatCard({ icon: Icon, label, value, color = 'accent' }) {
  const colorClasses = {
    accent: 'bg-accent/10 text-accent',
    green: 'bg-green-500/10 text-green-400',
    blue: 'bg-blue-500/10 text-blue-400',
    purple: 'bg-purple-500/10 text-purple-400',
    yellow: 'bg-yellow-500/10 text-yellow-400',
  };
  
  return (
    <div className="card p-6">
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

// Badge
export function Badge({ children, color = 'gray' }) {
  const colorClasses = {
    gray: 'bg-surface-700 text-surface-300',
    green: 'bg-green-500/20 text-green-400',
    blue: 'bg-blue-500/20 text-blue-400',
    purple: 'bg-purple-500/20 text-purple-400',
    yellow: 'bg-yellow-500/20 text-yellow-400',
    red: 'bg-red-500/20 text-red-400',
  };
  
  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${colorClasses[color]}`}>
      {children}
    </span>
  );
}

// Status Indicator
export function StatusIndicator({ online, showLabel = false }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`w-2 h-2 rounded-full ${online ? 'bg-green-500' : 'bg-surface-600'}`} />
      {showLabel && (
        <span className={`text-sm ${online ? 'text-green-400' : 'text-surface-500'}`}>
          {online ? 'Online' : 'Offline'}
        </span>
      )}
    </div>
  );
}

// Color Dot
export function ColorDot({ color, size = 'md' }) {
  const sizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };
  
  return (
    <span 
      className={`${sizeClasses[size]} rounded-full flex-shrink-0`}
      style={{ backgroundColor: color }}
    />
  );
}

// Modal
export function Modal({ isOpen, onClose, title, children, size = 'md' }) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);
  
  if (!isOpen) return null;
  
  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />
      <div className={`relative bg-surface-900 border border-surface-700 rounded-2xl w-full ${sizeClasses[size]} max-h-[90vh] overflow-auto`}>
        <div className="flex items-center justify-between p-6 border-b border-surface-800">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} className="p-2 hover:bg-surface-800 rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

// Confirm Dialog
export function ConfirmDialog({ isOpen, onClose, onConfirm, title, message, confirmText = 'Confirm', danger = false }) {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />
      <div className="relative bg-surface-900 border border-surface-700 rounded-2xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold mb-2">{title}</h2>
        <p className="text-surface-400 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="btn btn-secondary">Cancel</button>
          <button onClick={() => { onConfirm(); onClose(); }} className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

// Toast
export function Toast({ message, type = 'info', onClose, duration = 4000 }) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [onClose, duration]);
  
  const typeClasses = {
    success: 'bg-green-500/20 border-green-500/30 text-green-400',
    error: 'bg-red-500/20 border-red-500/30 text-red-400',
    info: 'bg-blue-500/20 border-blue-500/30 text-blue-400',
  };
  
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    info: AlertCircle,
  };
  
  const Icon = icons[type];
  
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${typeClasses[type]}`}>
        <Icon className="w-5 h-5" />
        <span>{message}</span>
        <button onClick={onClose} className="p-1 hover:bg-white/10 rounded">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// Select
export function Select({ value, onChange, options, placeholder }) {
  return (
    <select 
      value={value} 
      onChange={e => onChange(e.target.value)}
      className="input"
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map(opt => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  );
}

// Upload Zone
export function UploadZone({ onFilesSelected, uploading = false, accept = '*', maxFiles = 10, compact = false }) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);
  
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files).slice(0, maxFiles);
      onFilesSelected(files);
    }
  };
  
  const handleChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files).slice(0, maxFiles);
      onFilesSelected(files);
    }
  };
  
  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`
        border-2 border-dashed rounded-xl cursor-pointer transition-all
        ${compact ? 'p-4' : 'p-8'}
        ${dragActive 
          ? 'border-accent bg-accent/10' 
          : 'border-surface-700 hover:border-surface-500 bg-surface-800/50'
        }
        ${uploading ? 'opacity-50 pointer-events-none' : ''}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={maxFiles > 1}
        onChange={handleChange}
        className="hidden"
      />
      
      <div className="flex flex-col items-center text-center">
        {uploading ? (
          <>
            <Loader2 className={`${compact ? 'w-6 h-6' : 'w-10 h-10'} text-accent animate-spin mb-2`} />
            <p className="text-surface-400">Uploading...</p>
          </>
        ) : (
          <>
            <Upload className={`${compact ? 'w-6 h-6' : 'w-10 h-10'} text-surface-500 mb-2`} />
            <p className={`text-surface-300 ${compact ? 'text-sm' : ''}`}>
              Drop files here or click to upload
            </p>
            {!compact && (
              <p className="text-sm text-surface-500 mt-1">
                Supports images and videos
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}