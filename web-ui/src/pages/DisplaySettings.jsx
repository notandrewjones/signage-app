import React, { useState } from 'react';
import { Image as ImageIcon, Upload, Trash2, Save, Plus, GripVertical } from 'lucide-react';
import { 
  useDefaultDisplay, updateDefaultDisplay, 
  uploadLogo, deleteLogo, uploadBackground, deleteBackground 
} from '../hooks/useApi';
import { 
  PageHeader, LoadingState, Toast, UploadZone, 
  ConfirmDialog, Select, Modal 
} from '../components/ui';

export default function DisplaySettings() {
  const { data: display, loading, refetch } = useDefaultDisplay();
  
  const [logoScale, setLogoScale] = useState(0.5);
  const [logoPosition, setLogoPosition] = useState('center');
  const [backgroundMode, setBackgroundMode] = useState('solid');
  const [backgroundColor, setBackgroundColor] = useState('#000000');
  const [slideshowDuration, setSlideshowDuration] = useState(30);
  const [slideshowTransition, setSlideshowTransition] = useState('fade');
  
  const [saving, setSaving] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [uploadingBg, setUploadingBg] = useState(false);
  const [deleteLogoConfirm, setDeleteLogoConfirm] = useState(false);
  const [deleteBgConfirm, setDeleteBgConfirm] = useState(null);
  const [toast, setToast] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [initialized, setInitialized] = useState(false);
  
  // Initialize form
  React.useEffect(() => {
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
      await updateDefaultDisplay({
        logo_scale: logoScale,
        logo_position: logoPosition,
        background_mode: backgroundMode,
        background_color: backgroundColor,
        slideshow_duration: slideshowDuration,
        slideshow_transition: slideshowTransition,
      });
      setToast({ message: 'Settings saved', type: 'success' });
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
      setToast({ message: 'Logo removed', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  const handleBackgroundUpload = async (files) => {
    setUploadingBg(true);
    try {
      for (const file of files) {
        await uploadBackground(file);
      }
      setToast({ message: `${files.length} background(s) uploaded`, type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    } finally {
      setUploadingBg(false);
    }
  };
  
  const handleDeleteBackground = async (id) => {
    try {
      await deleteBackground(id);
      setToast({ message: 'Background removed', type: 'success' });
      refetch();
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };
  
  if (loading || !display) {
    return <LoadingState message="Loading display settings..." />;
  }
  
  return (
    <div>
      <PageHeader 
        title="Default Display" 
        description="Configure what shows when no content is scheduled"
        actions={
          <div className="flex items-center gap-3">
            <button onClick={() => setShowPreview(true)} className="btn btn-secondary">
              Preview
            </button>
            <button onClick={handleSave} className="btn btn-primary" disabled={saving}>
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        }
      />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Logo Settings */}
        <div className="card p-6">
          <h2 className="section-title">Logo</h2>
          <p className="text-sm text-surface-400 mb-6">
            Upload a logo to display when no content is scheduled. Supports PNG with transparency.
          </p>
          
          {display.logo_url ? (
            <div className="space-y-4">
              <div className="relative aspect-video bg-surface-800 rounded-lg overflow-hidden flex items-center justify-center">
                <img 
                  src={display.logo_url} 
                  alt="Logo" 
                  className="max-w-full max-h-full object-contain"
                  style={{ transform: `scale(${logoScale})` }}
                />
              </div>
              
              <div className="flex items-center gap-3">
                <UploadZone onFilesSelected={handleLogoUpload} accept="image/*" multiple={false}>
                  <span className="btn btn-secondary">
                    {uploadingLogo ? 'Uploading...' : 'Replace Logo'}
                  </span>
                </UploadZone>
                <button 
                  onClick={() => setDeleteLogoConfirm(true)}
                  className="btn btn-danger"
                >
                  <Trash2 className="w-4 h-4" />
                  Remove
                </button>
              </div>
            </div>
          ) : (
            <UploadZone onFilesSelected={handleLogoUpload} accept="image/*" multiple={false}>
              <ImageIcon className="w-10 h-10 text-surface-500 mx-auto mb-3" />
              <p className="text-surface-300 font-medium">
                {uploadingLogo ? 'Uploading...' : 'Drop logo here or click to upload'}
              </p>
              <p className="text-sm text-surface-500 mt-1">
                PNG recommended for transparency support
              </p>
            </UploadZone>
          )}
          
          <div className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">
                Logo Scale: {Math.round(logoScale * 100)}%
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
              <label className="block text-sm font-medium text-surface-300 mb-2">
                Logo Position
              </label>
              <Select
                value={logoPosition}
                onChange={setLogoPosition}
                options={[
                  { value: 'center', label: 'Center' },
                  { value: 'top', label: 'Top' },
                  { value: 'bottom', label: 'Bottom' },
                ]}
              />
            </div>
          </div>
        </div>
        
        {/* Background Settings */}
        <div className="card p-6">
          <h2 className="section-title">Background</h2>
          <p className="text-sm text-surface-400 mb-6">
            Choose a background to display behind your logo.
          </p>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-surface-300 mb-2">
                Background Mode
              </label>
              <Select
                value={backgroundMode}
                onChange={setBackgroundMode}
                options={[
                  { value: 'solid', label: 'Solid Color' },
                  { value: 'image', label: 'Single Image' },
                  { value: 'slideshow', label: 'Slideshow' },
                ]}
              />
            </div>
            
            {backgroundMode === 'solid' && (
              <div>
                <label className="block text-sm font-medium text-surface-300 mb-2">
                  Background Color
                </label>
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
                    className="input w-32 font-mono"
                  />
                </div>
              </div>
            )}
            
            {(backgroundMode === 'image' || backgroundMode === 'slideshow') && (
              <>
                <div>
                  <label className="block text-sm font-medium text-surface-300 mb-2">
                    Background Images
                  </label>
                  
                  <UploadZone 
                    onFilesSelected={handleBackgroundUpload} 
                    accept="image/*"
                    multiple={backgroundMode === 'slideshow'}
                  >
                    <Plus className="w-6 h-6 text-surface-500 mx-auto mb-2" />
                    <p className="text-sm text-surface-400">
                      {uploadingBg ? 'Uploading...' : 'Add background images'}
                    </p>
                  </UploadZone>
                  
                  {display.backgrounds?.length > 0 && (
                    <div className="grid grid-cols-3 gap-3 mt-4">
                      {display.backgrounds.map((bg) => (
                        <div key={bg.id} className="relative group aspect-video rounded-lg overflow-hidden bg-surface-800">
                          <img 
                            src={bg.url} 
                            alt="" 
                            className="w-full h-full object-cover"
                          />
                          <button
                            onClick={() => setDeleteBgConfirm(bg)}
                            className="absolute top-2 right-2 p-1.5 bg-red-500/80 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Trash2 className="w-4 h-4 text-white" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                {backgroundMode === 'slideshow' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-surface-300 mb-2">
                        Slide Duration: {slideshowDuration}s
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
                      <label className="block text-sm font-medium text-surface-300 mb-2">
                        Transition
                      </label>
                      <Select
                        value={slideshowTransition}
                        onChange={setSlideshowTransition}
                        options={[
                          { value: 'fade', label: 'Fade' },
                          { value: 'slide', label: 'Slide' },
                          { value: 'none', label: 'None' },
                        ]}
                      />
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>
      
      <ConfirmDialog
        isOpen={deleteLogoConfirm}
        onClose={() => setDeleteLogoConfirm(false)}
        onConfirm={handleDeleteLogo}
        title="Remove Logo"
        message="Are you sure you want to remove the logo?"
        confirmText="Remove"
        danger
      />
      
      <ConfirmDialog
        isOpen={!!deleteBgConfirm}
        onClose={() => setDeleteBgConfirm(null)}
        onConfirm={() => handleDeleteBackground(deleteBgConfirm.id)}
        title="Remove Background"
        message="Remove this background image?"
        confirmText="Remove"
        danger
      />
      
      {showPreview && (
        <PreviewModal 
          display={display}
          logoScale={logoScale}
          logoPosition={logoPosition}
          backgroundMode={backgroundMode}
          backgroundColor={backgroundColor}
          onClose={() => setShowPreview(false)}
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

function PreviewModal({ display, logoScale, logoPosition, backgroundMode, backgroundColor, onClose }) {
  const positionClasses = {
    top: 'items-start pt-20',
    center: 'items-center',
    bottom: 'items-end pb-20',
  };
  
  const backgroundStyle = backgroundMode === 'solid' 
    ? { backgroundColor }
    : display.backgrounds?.[0]?.url 
      ? { backgroundImage: `url(${display.backgrounds[0].url})`, backgroundSize: 'cover', backgroundPosition: 'center' }
      : { backgroundColor: '#000' };
  
  return (
    <Modal isOpen={true} onClose={onClose} title="Preview" size="xl">
      <div 
        className={`aspect-video rounded-lg overflow-hidden flex justify-center ${positionClasses[logoPosition]}`}
        style={backgroundStyle}
      >
        {display.logo_url && (
          <img 
            src={display.logo_url}
            alt="Logo"
            className="max-h-full object-contain"
            style={{ transform: `scale(${logoScale})` }}
          />
        )}
      </div>
      <p className="text-sm text-surface-400 text-center mt-4">
        This is how your default display will appear when no content is scheduled
      </p>
    </Modal>
  );
}
