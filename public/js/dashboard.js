// Dashboard page JavaScript

let permits = [];
let rivers = [];
let currentEditId = null;

document.addEventListener('DOMContentLoaded', async () => {
  // Check authentication
  await checkAuth();

  // Load rivers and permits
  await loadRivers();
  await loadPermits();

  // Setup event listeners
  setupEventListeners();
});

async function checkAuth() {
  try {
    const response = await fetch('/api/auth/me');
    if (!response.ok) {
      window.location.href = '/login.html';
      return;
    }
    const data = await response.json();
    document.getElementById('userEmail').textContent = data.user.email;

    // Hide admin link if user is not admin
    if (!data.user.isAdmin) {
      const adminLink = document.querySelector('a[href="/admin.html"]');
      if (adminLink) {
        adminLink.style.display = 'none';
      }
    }
  } catch (error) {
    window.location.href = '/login.html';
  }
}

async function loadRivers() {
  try {
    const response = await fetch('/api/permits/rivers');
    const data = await response.json();
    rivers = data.rivers;

    // Populate river select
    const select = document.getElementById('riverSelect');
    select.innerHTML = '<option value="">Select a river...</option>';
    rivers.forEach(river => {
      const option = document.createElement('option');
      option.value = river.id;
      option.textContent = `${river.name} - ${river.location}`;
      option.dataset.name = river.name;
      option.dataset.location = river.location;
      select.appendChild(option);
    });
  } catch (error) {
    console.error('Failed to load rivers:', error);
  }
}

async function loadPermits() {
  try {
    const response = await fetch('/api/permits');
    const data = await response.json();
    permits = data.permits;
    renderPermits();
  } catch (error) {
    console.error('Failed to load permits:', error);
    showError('Failed to load permits');
  }
}

function renderPermits() {
  const container = document.getElementById('permitsContainer');

  if (permits.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <h3>No permit monitors yet</h3>
        <p>Click "Add New Permit" to start monitoring river permits</p>
      </div>
    `;
    return;
  }

  container.innerHTML = permits.map(permit => {
    const river = rivers.find(r => r.id === permit.facility_id);
    const statusBadge = permit.enabled
      ? '<span class="badge badge-success">Active</span>'
      : '<span class="badge badge-secondary">Paused</span>';

    return `
      <div class="permit-card">
        <div class="permit-header">
          <div>
            <div class="permit-title">${permit.name}</div>
            <div class="permit-location">${river ? river.location : `Facility ${permit.facility_id}`}</div>
          </div>
          <div class="permit-actions">
            ${statusBadge}
            <button class="icon-btn" onclick="editPermit(${permit.id})" title="Edit">
              ✏️
            </button>
            <button class="icon-btn" onclick="togglePermit(${permit.id}, ${!permit.enabled})" title="${permit.enabled ? 'Pause' : 'Resume'}">
              ${permit.enabled ? '⏸️' : '▶️'}
            </button>
            <button class="icon-btn" onclick="deletePermit(${permit.id})" title="Delete">
              🗑️
            </button>
          </div>
        </div>
        <div class="permit-details">
          <div class="detail-item">
            <div class="detail-label">Date Range</div>
            <div class="detail-value">${formatDate(permit.start_date)} - ${formatDate(permit.end_date)}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">Party Size</div>
            <div class="detail-value">${permit.party_size} people</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">Created</div>
            <div class="detail-value">${formatDateTime(permit.created_at)}</div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function setupEventListeners() {
  // Logout
  document.getElementById('logoutBtn').addEventListener('click', logout);

  // Add permit button
  document.getElementById('addPermitBtn').addEventListener('click', () => {
    currentEditId = null;
    document.getElementById('modalTitle').textContent = 'Add Permit Monitor';
    document.getElementById('permitForm').reset();
    document.getElementById('permitId').value = '';
    showModal('permitModal');
  });

  // Permit form submit
  document.getElementById('permitForm').addEventListener('submit', savePermit);

  // Modal close buttons
  document.querySelectorAll('.close').forEach(btn => {
    btn.addEventListener('click', function() {
      closeModal(this.closest('.modal').id);
    });
  });

  document.querySelectorAll('.cancel-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      closeModal(this.closest('.modal').id);
    });
  });

  // Delete confirmation
  document.querySelector('.confirm-delete').addEventListener('click', confirmDelete);
  document.querySelector('.cancel-delete').addEventListener('click', () => {
    closeModal('deleteModal');
  });

  // River select change - auto-fill name
  document.getElementById('riverSelect').addEventListener('change', function() {
    const permitName = document.getElementById('permitName');
    if (!permitName.value && this.selectedOptions[0]) {
      const riverName = this.selectedOptions[0].dataset.name;
      if (riverName) {
        permitName.value = riverName;
      }
    }
  });

  // Set default date range (next 6 months)
  const today = new Date();
  const sixMonthsLater = new Date();
  sixMonthsLater.setMonth(today.getMonth() + 6);

  document.getElementById('startDate').value = today.toISOString().split('T')[0];
  document.getElementById('endDate').value = sixMonthsLater.toISOString().split('T')[0];
}

async function savePermit(e) {
  e.preventDefault();

  const formData = {
    name: document.getElementById('permitName').value.trim() ||
          document.getElementById('riverSelect').selectedOptions[0]?.dataset.name ||
          'Unnamed Permit',
    facility_id: document.getElementById('riverSelect').value,
    start_date: document.getElementById('startDate').value,
    end_date: document.getElementById('endDate').value,
    party_size: parseInt(document.getElementById('partySize').value),
    enabled: document.getElementById('enabled').checked
  };

  const permitId = document.getElementById('permitId').value;
  const isEdit = permitId !== '';

  try {
    const response = await fetch(
      isEdit ? `/api/permits/${permitId}` : '/api/permits',
      {
        method: isEdit ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      }
    );

    const data = await response.json();

    if (response.ok) {
      closeModal('permitModal');
      await loadPermits();
    } else {
      showFormError(data.error || 'Failed to save permit');
    }
  } catch (error) {
    console.error('Save error:', error);
    showFormError('Network error. Please try again.');
  }
}

function editPermit(id) {
  const permit = permits.find(p => p.id === id);
  if (!permit) return;

  currentEditId = id;
  document.getElementById('modalTitle').textContent = 'Edit Permit Monitor';
  document.getElementById('permitId').value = id;
  document.getElementById('riverSelect').value = permit.facility_id;
  document.getElementById('permitName').value = permit.name;
  document.getElementById('startDate').value = permit.start_date;
  document.getElementById('endDate').value = permit.end_date;
  document.getElementById('partySize').value = permit.party_size;
  document.getElementById('enabled').checked = permit.enabled;

  showModal('permitModal');
}

let deleteId = null;

function deletePermit(id) {
  deleteId = id;
  showModal('deleteModal');
}

async function confirmDelete() {
  if (!deleteId) return;

  try {
    const response = await fetch(`/api/permits/${deleteId}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      closeModal('deleteModal');
      await loadPermits();
    } else {
      const data = await response.json();
      alert(data.error || 'Failed to delete permit');
    }
  } catch (error) {
    console.error('Delete error:', error);
    alert('Network error. Please try again.');
  }
}

async function togglePermit(id, enabled) {
  try {
    const response = await fetch(`/api/permits/${id}/toggle`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });

    if (response.ok) {
      await loadPermits();
    } else {
      const data = await response.json();
      alert(data.error || 'Failed to update permit');
    }
  } catch (error) {
    console.error('Toggle error:', error);
    alert('Network error. Please try again.');
  }
}

async function logout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login.html';
  } catch (error) {
    console.error('Logout error:', error);
    window.location.href = '/login.html';
  }
}

function showModal(modalId) {
  document.getElementById(modalId).classList.add('show');
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove('show');
  document.getElementById('formError')?.setAttribute('style', 'display: none');
}

function showFormError(message) {
  const errorDiv = document.getElementById('formError');
  errorDiv.textContent = message;
  errorDiv.style.display = 'block';
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateTime(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function showError(message) {
  // Could implement a toast notification here
  console.error(message);
}
