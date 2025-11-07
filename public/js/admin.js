// Admin page JavaScript

let users = [];

document.addEventListener('DOMContentLoaded', async () => {
  // Check authentication
  await checkAuth();

  // Load users
  await loadUsers();

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

    // Redirect non-admin users to dashboard
    if (!data.user.isAdmin) {
      window.location.href = '/dashboard.html';
      return;
    }
  } catch (error) {
    window.location.href = '/login.html';
  }
}

async function loadUsers() {
  try {
    const response = await fetch('/api/admin/users');
    const data = await response.json();
    users = data.users;
    renderUsers();
  } catch (error) {
    console.error('Failed to load users:', error);
    showError('Failed to load users');
  }
}

function renderUsers() {
  const container = document.getElementById('usersContainer');

  if (users.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <h3>No users yet</h3>
        <p>Click "Create User" to add your first user</p>
      </div>
    `;
    return;
  }

  container.innerHTML = users.map(user => {
    const statusBadge = user.is_active
      ? '<span class="badge badge-success">Active</span>'
      : '<span class="badge badge-warning">Inactive</span>';

    const activateBtn = user.is_active
      ? `<button class="btn btn-sm btn-secondary" onclick="deactivateUser(${user.id})">Deactivate</button>`
      : `<button class="btn btn-sm btn-success" onclick="activateUser(${user.id})">Activate</button>`;

    return `
      <div class="user-card">
        <div class="user-header">
          <div>
            <div class="user-title">${user.email}</div>
            <div class="user-email-text">Created: ${formatDateTime(user.created_at)}</div>
          </div>
          <div class="user-actions">
            ${statusBadge}
            ${activateBtn}
            <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})">Delete</button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function setupEventListeners() {
  // Logout
  document.getElementById('logoutBtn').addEventListener('click', logout);

  // Add user button
  document.getElementById('addUserBtn').addEventListener('click', () => {
    document.getElementById('userForm').reset();
    document.getElementById('userActive').checked = true;
    showModal('userModal');
  });

  // User form submit
  document.getElementById('userForm').addEventListener('submit', createUser);

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
}

async function createUser(e) {
  e.preventDefault();

  const formData = {
    email: document.getElementById('userEmail').value.trim(),
    password: document.getElementById('userPassword').value,
    is_active: document.getElementById('userActive').checked
  };

  try {
    const response = await fetch('/api/admin/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });

    const data = await response.json();

    if (response.ok) {
      closeModal('userModal');
      await loadUsers();
    } else {
      showFormError(data.error || 'Failed to create user');
    }
  } catch (error) {
    console.error('Create user error:', error);
    showFormError('Network error. Please try again.');
  }
}

async function activateUser(id) {
  try {
    const response = await fetch(`/api/admin/users/${id}/activate`, {
      method: 'PATCH'
    });

    if (response.ok) {
      await loadUsers();
    } else {
      const data = await response.json();
      alert(data.error || 'Failed to activate user');
    }
  } catch (error) {
    console.error('Activate error:', error);
    alert('Network error. Please try again.');
  }
}

async function deactivateUser(id) {
  try {
    const response = await fetch(`/api/admin/users/${id}/deactivate`, {
      method: 'PATCH'
    });

    if (response.ok) {
      await loadUsers();
    } else {
      const data = await response.json();
      alert(data.error || 'Failed to deactivate user');
    }
  } catch (error) {
    console.error('Deactivate error:', error);
    alert('Network error. Please try again.');
  }
}

async function deleteUser(id) {
  if (!confirm('Are you sure you want to delete this user? This will also delete all their permit monitors.')) {
    return;
  }

  try {
    const response = await fetch(`/api/admin/users/${id}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      await loadUsers();
    } else {
      const data = await response.json();
      alert(data.error || 'Failed to delete user');
    }
  } catch (error) {
    console.error('Delete error:', error);
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
  document.getElementById('userFormError')?.setAttribute('style', 'display: none');
}

function showFormError(message) {
  const errorDiv = document.getElementById('userFormError');
  errorDiv.textContent = message;
  errorDiv.style.display = 'block';
}

function formatDateTime(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function showError(message) {
  console.error(message);
}
