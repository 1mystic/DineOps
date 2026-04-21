const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

async function post(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export const runForecast = (datasetId, horizon = 24) => post('/v1/forecast/run', { dataset_id: datasetId, horizon });

export const optimizeStaffing = (datasetId) => post('/v1/optimize/staffing', { dataset_id: datasetId });

export const optimizeInventory = (datasetId) => post('/v1/optimize/inventory', { dataset_id: datasetId });

export const optimizePricing = (datasetId) => post('/v1/optimize/pricing', { dataset_id: datasetId });

export const generateReport = (datasetId) => post('/v1/report/generate', { dataset_id: datasetId, focus: 'operations' });

export const syncExternal = (datasetId, locationId, startDate, endDate) =>
  post('/v1/external/sync', {
    dataset_id: datasetId,
    location_id: locationId,
    start_date: startDate,
    end_date: endDate,
  });
