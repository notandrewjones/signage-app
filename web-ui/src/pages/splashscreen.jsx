import React, { useState, useEffect, useRef } from 'react';
import { 
  Save, Upload, Trash2, Image, Video, Plus, GripVertical,
  Monitor, Palette
} from 'lucide-react';
import { 
  useSplashScreen, updateSplashScreen, uploadLogo, deleteLogo,
  uploadBackground, deleteBackground, uploadBackgroundVideo, deleteBackgroundVideo
} from '../hooks/useApi';
import { 
  PageHeader, LoadingState, ConfirmDialog, Toast, UploadZone,
} from '../components/ui';

export default function SplashScreen() {
  const { data: display, loading, refetch } = useSplashScreen();
  const videoInputRef = useRef(null);
  
  const [logoScale, setLogoScale] = useState(0.5);
  const [logoPosition, setLogoPosition] = useState('center');
  const [backgroundMode, setBackgroundMode] = useState('solid');
  const [backgroundColor, setBackgroundColor] = useState('#000000');
  const [slideshowDuration, setSlideshowDuration] = useState(30);
  const [slideshowTransition, setSlideshowTransition] = useState('fade');
  
  const [saving, setSaving] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [uploadingBackground, setUploadingBackground] = useState(false);
  const [uploadingVideo, setUploadingVideo] = useState(false);
  const [deleteLogoConfirm, setDeleteLogoConfirm] = useState(false);
  const [deleteBackgroundConfirm, setDeleteBackgroundConfirm] = useState(null);
  const [deleteVideoConfirm, setDeleteVideoConfirm] = useState(false);
  const [toast, setToast] = useState(null);
  const [initialized, setInitialized] = useState(false);
  
  useEffect(() => {
    if (display && !initialized) {
      setLogoScale(display.logo_scale);
      setLogoPosition(display.logo_position);
      setBackgroundMode(display.background_mode);
      setBackgroundColor(display.background_color);
      setSlideshowDuration(display.slideshow_duration);
      setSlideshowTransition(display.slideshow_transition);
      setInitialized(true);
    }
  }, [display, initialized]);
  
  const handleSave = async () => {
    setSaving(true);
    try {
      await updateSplashScreen({
        logo_scale: logoScale,
        logo_position: logoPosition,
        background_mode: backgroundMode,
        background_color: backgroundColor,
        slideshow_duration: slideshowDuration,
        slideshow_transition: slideshowTransition,
      });
      setToast({ message: 'Splash screen settings saved', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    } finally {
      setSaving(false);
    }
  };
  
  const handleLogoUpload = async (files) => {
    if (files.length === 0) return;
    setUploadingLogo(true);
    try {
      await uploadLogo(files[0]);
      setToast({ message: 'Logo uploaded', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    } finally {
      setUploadingLogo(false);
    }
  };
  
  const handleDeleteLogo = async () => {
    try {
      await deleteLogo();
      setToast({ message: 'Logo deleted', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleBackgroundUpload = async (files) => {
    setUploadingBackground(true);
    try {
      for (const file of files) {
        await uploadBackground(file);
      }
      setToast({ message: `${files.length} background(s) uploaded`, type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    } finally {
      setUploadingBackground(false);
    }
  };
  
  const handleDeleteBackground = async (id) => {
    try {
      await deleteBackground(id);
      setDeleteBackgroundConfirm(null);
      setToast({ message: 'Background deleted', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleVideoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploadingVideo(true);
    try {
      await uploadBackgroundVideo(file);
      setToast({ message: 'Background video uploaded', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    } finally {
      setUploadingVideo(false);
    }
  };
  
  const handleDeleteVideo = async () => {
    try {
      await deleteBackgroundVideo();
      setDeleteVideoConfirm(false);
      setToast({ message: 'Background video deleted', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  if (loading) {
    return <LoadingState message="Loading splash screen settings..." />;
  }
  
  return (
    <div>
      <PageHeader 
        title="Splash Screen"
        description="Customize what displays when no content is scheduled"
        actions={
          <button onClick={handleSave} className="btn btn-primary" disabled={saving}>
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        }
      />
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Preview */}
        <div className="lg:col-span-2">
          <div className="card p-6">
            <h2 className="section-title flex items-center gap-2">
              <Monitor className="w-5 h-5" />
              Preview
            </h2>
            <div 
              className="relative aspect-video rounded-xl overflow-hidden border-2 border-surface-700"
              style={{ 
                backgroundColor: backgroundMode === 'solid' ? backgroundColor : '#000'
              }}
            >
              {/* Background based on mode */}
              {backgroundMode === 'image' && display?.backgrounds?.[0] && (
                <img 
                  src={display.backgrounds[0].url} 
                  alt="Background" 
                  className="absolute inset-0 w-full h-full object-cover"
                />
              )}
              {backgroundMode === 'video' && display?.background_video_url && (
                <video 
                  src={display.background_video_url} 
                  className="absolute inset-0 w-full h-full object-cover"
                  autoPlay
                  muted
                  loop
                  playsInline
                />
              )}
              {backgroundMode === 'slideshow' && display?.backgrounds?.length > 0 && (
                <img 
                  src={display.backgrounds[0].url} 
                  alt="Background" 
                  className="absolute inset-0 w-full h-full object-cover"
                />
              )}
              
              {/* Logo overlay */}
              {display?.logo_url && (
                <div className={`absolute inset-0 flex ${
                  logoPosition === 'top' ? 'items-start pt-8' :
                  logoPosition === 'bottom' ? 'items-end pb-8' :
                  'items-center'
                } justify-center`}>
                  <img 
                    src={display.logo_url} 
                    alt="Logo" 
                    style={{ 
                      maxWidth: `${logoScale * 100}%`,
                      maxHeight: `${logoScale * 80}%`,
                      objectFit: 'contain'
                    }}
                  />
                </div>
              )}
              
              {!display?.logo_url && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <p className="text-surface-500">No logo uploaded</p>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Settings sidebar */}
        <div className="space-y-6">
          {/* Logo Settings */}
          <div className="card p-6">
            <h2 className="section-title">Logo</h2>
            
            {display?.logo_url ? (
              <div className="space-y-4">
                <div className="relative group">
                  <img 
                    src={display.logo_url} 
                    alt="Current logo" 
                    className="w-full h-32 object-contain bg-surface-800 rounded-lg"
                  />
                  <button 
                    onClick={() => setDeleteLogoConfirm(true)}
                    className="absolute top-2 right-2 btn btn-icon btn-danger opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-surface-300 mb-2">
                    Logo Size: {Math.round(logoScale * 100)}%
                  </label>
                  <input 
                    type="range" 
                    min="0.1" 
                    max="1" 
                    step="0.05" 
                    value={logoScale} 
                    onChange={e => setLogoScale(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-surface-300 mb-2">Position</label>
                  <div className="grid grid-cols-3 gap-2">
                    {['top', 'center', 'bottom'].map(pos => (
                      <button
                        key={pos}
                        onClick={() => setLogoPosition(pos)}
                        className={`px-3 py-2 rounded-lg text-sm capitalize transition-colors ${
                          logoPosition === pos 
                            ? 'bg-accent text-white' 
                            : 'bg-surface-800 text-surface-400 hover:bg-surface-700'
                        }`}
                      >
                        {pos}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <UploadZone 
                onFilesSelected={handleLogoUpload} 
                uploading={uploadingLogo}
                accept="image/*"
                maxFiles={1}
                compact
              />
            )}
          </div>
          
          {/* Background Mode */}
          <div className="card p-6">
            <h2 className="section-title flex items-center gap-2">
              <Palette className="w-5 h-5" />
              Background
            </h2>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2">
                {[
                  { value: 'solid', label: 'Solid Color', icon: Palette },
                  { value: 'image', label: 'Image', icon: Image },
                  { value: 'video', label: 'Video', icon: Video },
                  { value: 'slideshow', label: 'Slideshow', icon: Image },
                ].map(({ value, label, icon: Icon }) => (
                  <button
                    key={value}
                    onClick={() => setBackgroundMode(value)}
                    className={`flex items-center gap-2 p-3 rounded-lg text-sm transition-colors ${
                      backgroundMode === value 
                        ? 'bg-accent text-white' 
                        : 'bg-surface-800 text-surface-400 hover:bg-surface-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {label}
                  </button>
                ))}
              </div>
              
              {/* Mode-specific settings */}
              {backgroundMode === 'solid' && (
                <div>
                  <label className="block text-sm font-medium text-surface-300 mb-2">Color</label>
                  <div className="flex items-center gap-3">
                    <input 
                      type="color" 
                      value={backgroundColor} 
                      onChange={e => setBackgroundColor(e.target.value)}
                      className="w-12 h-12 rounded-lg cursor-pointer"
                    />
                    <input 
                      type="text" 
                      value={backgroundColor} 
                      onChange={e => setBackgroundColor(e.target.value)}
                      className="input flex-1 font-mono"
                    />
                  </div>
                </div>
              )}
              
              {backgroundMode === 'video' && (
                <div className="space-y-3">
                  {display?.background_video_url ? (
                    <div className="relative group">
                      <video 
                        src={display.background_video_url} 
                        className="w-full h-32 object-cover bg-surface-800 rounded-lg"
                        muted
                        loop
                        autoPlay
                        playsInline
                      />
                      <button 
                        onClick={() => setDeleteVideoConfirm(true)}
                        className="absolute top-2 right-2 btn btn-icon btn-danger opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <div>
                      <input 
                        type="file" 
                        ref={videoInputRef}
                        onChange={handleVideoUpload}
                        accept="video/*"
                        className="hidden"
                      />
                      <button 
                        onClick={() => videoInputRef.current?.click()}
                        disabled={uploadingVideo}
                        className="btn btn-secondary w-full"
                      >
                        <Video className="w-4 h-4" />
                        {uploadingVideo ? 'Uploading...' : 'Upload Video'}
                      </button>
                    </div>
                  )}
                  <p className="text-xs text-surface-500">
                    Video will loop continuously in the background
                  </p>
                </div>
              )}
              
              {(backgroundMode === 'image' || backgroundMode === 'slideshow') && (
                <div className="space-y-3">
                  <UploadZone 
                    onFilesSelected={handleBackgroundUpload} 
                    uploading={uploadingBackground}
                    accept="image/*"
                    compact
                  />
                  
                  {display?.backgrounds?.length > 0 && (
                    <div className="space-y-2">
                      {display.backgrounds.map(bg => (
                        <div key={bg.id} className="flex items-center gap-3 p-2 bg-surface-800 rounded-lg group">
                          <img src={bg.url} alt="" className="w-16 h-10 object-cover rounded" />
                          <span className="flex-1 text-sm truncate">{bg.filename}</span>
                          <button 
                            onClick={() => setDeleteBackgroundConfirm(bg)}
                            className="btn btn-icon btn-ghost text-red-400 opacity-0 group-hover:opacity-100"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {backgroundMode === 'slideshow' && (
                    <div className="space-y-3 pt-3 border-t border-surface-700">
                      <div>
                        <label className="block text-sm font-medium text-surface-300 mb-2">
                          Duration: {slideshowDuration}s
                        </label>
                        <input 
                          type="range" 
                          min="5" 
                          max="120" 
                          step="5" 
                          value={slideshowDuration} 
                          onChange={e => setSlideshowDuration(parseInt(e.target.value))}
                          className="w-full"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-surface-300 mb-2">Transition</label>
                        <select 
                          value={slideshowTransition} 
                          onChange={e => setSlideshowTransition(e.target.value)}
                          className="input"
                        >
                          <option value="fade">Fade</option>
                          <option value="slide">Slide</option>
                          <option value="none">None</option>
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Confirm Dialogs */}
      <ConfirmDialog 
        isOpen={deleteLogoConfirm} 
        onClose={() => setDeleteLogoConfirm(false)} 
        onConfirm={handleDeleteLogo} 
        title="Delete Logo" 
        message="Are you sure you want to delete the logo?" 
        confirmText="Delete" 
        danger 
      />
      
      <ConfirmDialog 
        isOpen={!!deleteBackgroundConfirm} 
        onClose={() => setDeleteBackgroundConfirm(null)} 
        onConfirm={() => handleDeleteBackground(deleteBackgroundConfirm?.id)} 
        title="Delete Background" 
        message="Are you sure you want to delete this background image?" 
        confirmText="Delete" 
        danger 
      />
      
      <ConfirmDialog 
        isOpen={deleteVideoConfirm} 
        onClose={() => setDeleteVideoConfirm(false)} 
        onConfirm={handleDeleteVideo} 
        title="Delete Video" 
        message="Are you sure you want to delete the background video?" 
        confirmText="Delete" 
        danger 
      />
      
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}