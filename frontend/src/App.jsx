import React, { useState } from 'react';
import {
  generateReport,
  optimizeInventory,
  optimizePricing,
  optimizeStaffing,
  runForecast,
  syncExternal,
} from './api';

function today() {
  return new Date().toISOString().slice(0, 10);
}

export default function App() {
  const [datasetId, setDatasetId] = useState('');
  const [locationId, setLocationId] = useState('LOC-1');
  const [startDate, setStartDate] = useState(today());
  const [endDate, setEndDate] = useState(today());

  const [forecast, setForecast] = useState(null);
  const [staffing, setStaffing] = useState(null);
  const [inventory, setInventory] = useState(null);
  const [pricing, setPricing] = useState(null);
  const [report, setReport] = useState(null);
  const [external, setExternal] = useState(null);
  const [error, setError] = useState('');

  const execute = async (fn, setter) => {
    setError('');
    try {
      const data = await fn();
      setter(data);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <main style={{ fontFamily: 'Arial', margin: 24, maxWidth: 1100 }}>
      <h1>DineOps Decision Intelligence</h1>
      <p>Iterative feature build: external sync + forecast + optimization + reporting.</p>

      <input
        value={datasetId}
        onChange={(e) => setDatasetId(e.target.value)}
        placeholder="dataset_id"
        style={{ width: '100%', padding: 10, marginBottom: 12 }}
      />

      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input value={locationId} onChange={(e) => setLocationId(e.target.value)} placeholder="location_id" />
        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 16 }}>
        <button onClick={() => execute(() => syncExternal(datasetId, locationId, startDate, endDate), setExternal)}>
          Sync External Signals
        </button>
        <button onClick={() => execute(() => runForecast(datasetId, 24), setForecast)}>Run Forecast</button>
        <button onClick={() => execute(() => optimizeStaffing(datasetId), setStaffing)}>Optimize Staffing</button>
        <button onClick={() => execute(() => optimizeInventory(datasetId), setInventory)}>Optimize Inventory</button>
        <button onClick={() => execute(() => optimizePricing(datasetId), setPricing)}>Optimize Pricing</button>
        <button onClick={() => execute(() => generateReport(datasetId), setReport)}>Generate Executive Report</button>
      </div>

      {error && <pre style={{ color: 'red', whiteSpace: 'pre-wrap' }}>{error}</pre>}

      {external && (
        <section>
          <h2>External Signals</h2>
          <pre>{JSON.stringify(external.signals.slice(0, 3), null, 2)}</pre>
        </section>
      )}

      {forecast && (
        <section>
          <h2>Forecast</h2>
          <p>Model Weights: {JSON.stringify(forecast.model_weights)}</p>
          <pre>{JSON.stringify(forecast.points.slice(0, 5), null, 2)}</pre>
        </section>
      )}

      {staffing && (
        <section>
          <h2>Staffing Recommendations</h2>
          <pre>{JSON.stringify(staffing.recommendations.slice(0, 5), null, 2)}</pre>
        </section>
      )}

      {inventory && (
        <section>
          <h2>Inventory Recommendations</h2>
          <pre>{JSON.stringify(inventory.recommendations.slice(0, 5), null, 2)}</pre>
        </section>
      )}

      {pricing && (
        <section>
          <h2>Pricing Recommendations</h2>
          <pre>{JSON.stringify(pricing.recommendations.slice(0, 5), null, 2)}</pre>
        </section>
      )}

      {report && (
        <section>
          <h2>Executive Report</h2>
          <pre>{JSON.stringify(report, null, 2)}</pre>
        </section>
      )}
    </main>
  );
}
