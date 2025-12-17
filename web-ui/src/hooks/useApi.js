import { useState, useEffect, useCallback } from 'react';

const API_BASE = '/api';

// Generic fetch wrapper with error handling
async function apiFetch(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Request failed');
  }
  
  return response.json();
}

// Upload file helper
async function uploadFile(endpoint, file, additionalData = {}) {
  const formData = new FormData();
  formData.append('file', file);
  Object.entries(additionalData).forEach(([key, value]) => {
    formData.append(key, value);
  });
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || 'Upload failed');
  }
  
  return response.json();
}

// Generic data fetching hook
export function useApi(endpoint, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFetch(endpoint);
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [endpoint, ...deps]);
  
  useEffect(() => {
    refetch();
  }, [refetch]);
  
  return { data, loading, error, refetch };
}

// Stats
export function useStats() {
  return useApi('/stats');
}

// Content Groups
export function useContentGroups() {
  return useApi('/content-groups');
}

export function useContentGroup(id) {
  return useApi(`/content-groups/${id}`, [id]);
}

export async function createContentGroup(data) {
  return apiFetch('/content-groups', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateContentGroup(id, data) {
  return apiFetch(`/content-groups/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteContentGroup(id) {
  return apiFetch(`/content-groups/${id}`, {
    method: 'DELETE',
  });
}

// Content Items
export async function uploadContent(groupId, file, name, displayDuration = 10) {
  return uploadFile(`/content-groups/${groupId}/content`, file, {
    name,
    display_duration: displayDuration,
  });
}

export async function updateContentItem(id, data) {
  return apiFetch(`/content/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteContentItem(id) {
  return apiFetch(`/content/${id}`, {
    method: 'DELETE',
  });
}

export async function reorderContent(groupId, itemIds) {
  return apiFetch(`/content-groups/${groupId}/reorder`, {
    method: 'POST',
    body: JSON.stringify(itemIds),
  });
}

// Schedule Groups
export function useScheduleGroups() {
  return useApi('/schedule-groups');
}

export function useScheduleGroup(id) {
  return useApi(`/schedule-groups/${id}`, [id]);
}

export async function createScheduleGroup(data) {
  return apiFetch('/schedule-groups', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateScheduleGroup(id, data) {
  return apiFetch(`/schedule-groups/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteScheduleGroup(id) {
  return apiFetch(`/schedule-groups/${id}`, {
    method: 'DELETE',
  });
}

// Schedules
export async function createSchedule(data) {
  return apiFetch('/schedules', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateSchedule(id, data) {
  return apiFetch(`/schedules/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteSchedule(id) {
  return apiFetch(`/schedules/${id}`, {
    method: 'DELETE',
  });
}

// Devices
export function useDevices() {
  return useApi('/devices');
}

export function useDevice(id) {
  return useApi(`/devices/${id}`, [id]);
}

export async function createDevice(data) {
  return apiFetch('/devices', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateDevice(id, data) {
  return apiFetch(`/devices/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteDevice(id) {
  return apiFetch(`/devices/${id}`, {
    method: 'DELETE',
  });
}

export async function regenerateDeviceKey(id) {
  return apiFetch(`/devices/${id}/regenerate-key`, {
    method: 'POST',
  });
}

// Default Display
export function useDefaultDisplay() {
  return useApi('/default-display');
}

export async function updateDefaultDisplay(data) {
  return apiFetch('/default-display', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function uploadLogo(file) {
  return uploadFile('/default-display/logo', file);
}

export async function deleteLogo() {
  return apiFetch('/default-display/logo', {
    method: 'DELETE',
  });
}

export async function uploadBackground(file) {
  return uploadFile('/default-display/backgrounds', file);
}

export async function deleteBackground(id) {
  return apiFetch(`/default-display/backgrounds/${id}`, {
    method: 'DELETE',
  });
}
