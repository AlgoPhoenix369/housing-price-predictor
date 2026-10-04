const CLIENT_ID_KEY = 'housing_client_id';
const PAGE_SIZE = 5;

let history = [];
let visibleCount = PAGE_SIZE;
let memoryId = null; // used only if the browser blocks localStorage

const form = document.getElementById('predict-form');
const errorBox = document.getElementById('error');
const resultBox = document.getElementById('result');
const predictButton = document.getElementById('predict-button');

// Builds a random anonymous ID that matches the backend's allowed format
function generateId() {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return 'c_' + Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

// Returns this browser's anonymous ID, creating and saving one on first use
function getClientId() {
  try {
    let id = localStorage.getItem(CLIENT_ID_KEY);
    if (!id) {
      id = generateId();
      localStorage.setItem(CLIENT_ID_KEY, id);
    }
    return id;
  } catch {
    if (!memoryId) memoryId = generateId();
    return memoryId;
  }
}

// Sends a request to the backend with the visitor's ID attached and returns the JSON result
async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Client-Id': getClientId(),
      ...options.headers,
    },
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') {
        message = body.detail;
      } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
        const field = body.detail[0].loc?.slice(-1)[0];
        message = field ? `${field}: ${body.detail[0].msg}` : body.detail[0].msg;
      }
    } catch {
      // The error response had no JSON body, so keep the generic message
    }
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

const money = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = !message;
}

// Draws the history table, summary line and the Show more / Show less buttons
function renderHistory() {
  const tableEl = document.getElementById('history-table');
  const body = document.getElementById('history-body');
  const summary = document.getElementById('history-summary');
  const emptyEl = document.getElementById('history-empty');

  body.replaceChildren();
  const hasHistory = history.length > 0;
  tableEl.hidden = !hasHistory;
  emptyEl.hidden = hasHistory;
  document.getElementById('clear-history').hidden = !hasHistory;

  for (const item of history.slice(0, visibleCount)) {
    const row = document.createElement('tr');
    const cells = [
      new Date(item.created_at).toLocaleString(),
      item.purpose === 'buy' ? 'Buy' : 'Sell',
      item.zipcode,
      `${item.sqft_living} sqft`,
      `${item.no_of_bedrooms} bd / ${item.no_of_bathrooms} ba`,
      item.no_of_floors,
      `${item.house_age} yrs`,
      money.format(item.predicted_price),
    ];
    for (const value of cells) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.appendChild(cell);
    }
    body.appendChild(row);
  }

  if (hasHistory) {
    const prices = history.map((item) => item.predicted_price);
    const average = prices.reduce((sum, p) => sum + p, 0) / prices.length;
    summary.textContent =
      `${history.length} prediction${history.length === 1 ? '' : 's'} · ` +
      `average ${money.format(average)} · highest ${money.format(Math.max(...prices))} · ` +
      `lowest ${money.format(Math.min(...prices))}`;
  } else {
    summary.textContent = '';
  }

  document.getElementById('show-more').hidden = visibleCount >= history.length;
  document.getElementById('show-less').hidden = visibleCount <= PAGE_SIZE;
}

// Fetches the visitor's saved predictions and redraws the table
async function loadHistory() {
  history = await request('/api/history?limit=100');
  renderHistory();
}

// Sends the form to the API, shows the estimate and refreshes the history
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  showError('');
  predictButton.disabled = true;
  predictButton.textContent = 'Predicting...';

  const raw = Object.fromEntries(new FormData(form));
  const payload = Object.fromEntries(
    Object.entries(raw).map(([key, value]) => [key, key === 'purpose' ? value : Number(value)])
  );

  try {
    const result = await request('/api/predict', { method: 'POST', body: JSON.stringify(payload) });
    document.getElementById('result-price').textContent = money.format(result.predicted_price);
    document.getElementById('result-range').textContent =
      `Predicted range: ${money.format(result.range_low)} – ${money.format(result.range_high)}`;
    resultBox.hidden = false;
    visibleCount = PAGE_SIZE;
    await loadHistory();
  } catch (error) {
    resultBox.hidden = true;
    showError(error.message);
  } finally {
    predictButton.disabled = false;
    predictButton.textContent = 'Predict price';
  }
});

document.getElementById('show-more').addEventListener('click', () => {
  visibleCount += PAGE_SIZE;
  renderHistory();
});

document.getElementById('show-less').addEventListener('click', () => {
  visibleCount = PAGE_SIZE;
  renderHistory();
});

document.getElementById('clear-history').addEventListener('click', async () => {
  if (!window.confirm('Delete your whole prediction history?')) return;
  try {
    await request('/api/history', { method: 'DELETE' });
    history = [];
    visibleCount = PAGE_SIZE;
    renderHistory();
  } catch (error) {
    showError(error.message);
  }
});

loadHistory().catch((error) => showError(error.message));