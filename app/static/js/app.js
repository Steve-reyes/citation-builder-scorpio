// Citation Builder - Frontend JS
(function() {
  'use strict';

  // Show flash messages as toasts
  document.addEventListener('DOMContentLoaded', function() {
    const flashContainer = document.getElementById('flash-messages');
    if (flashContainer) {
      const alerts = flashContainer.querySelectorAll('.alert');
      alerts.forEach(function(el) {
        const type = el.classList.contains('alert-success') ? 'success'
                  : el.classList.contains('alert-danger') ? 'error'
                  : 'info';
        showToast(el.textContent.trim(), type);
        el.remove();
      });
    }
  });

  // Toast system
  window.showToast = function(message, type) {
    type = type || 'info';
    var container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    var icon = '';
    if (type === 'success') icon = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>';
    else if (type === 'error') icon = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>';
    else icon = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';
    toast.innerHTML = icon + '<span>' + message + '</span>';
    container.appendChild(toast);
    setTimeout(function() {
      toast.style.animation = 'slideOut 0.3s ease forwards';
      setTimeout(function() { toast.remove(); }, 300);
    }, 4000);
  };

  // API helper
  window.api = {
    get: function(url) {
      return fetch(url).then(function(r) { return r.json(); });
    },
    post: function(url, data) {
      return fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRF() },
        body: JSON.stringify(data)
      }).then(function(r) { return r.json(); });
    }
  };

  function getCSRF() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  // Confirm dialog
  window.confirmAction = function(message, callback) {
    var overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = '<div class="modal-content text-center">' +
      '<div class="text-2xl mb-4 text-yellow-400">⚠️</div>' +
      '<p class="text-gray-300 mb-6">' + (message || 'Are you sure?') + '</p>' +
      '<div class="flex gap-3 justify-center">' +
      '<button class="btn btn-outline btn-cancel">Cancel</button>' +
      '<button class="btn btn-danger btn-confirm">Confirm</button>' +
      '</div></div>';
    document.body.appendChild(overlay);
    overlay.querySelector('.btn-cancel').addEventListener('click', function() {
      overlay.remove();
    });
    overlay.querySelector('.btn-confirm').addEventListener('click', function() {
      overlay.remove();
      if (typeof callback === 'function') callback();
    });
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) overlay.remove();
    });
  };

  // Delete confirm on buttons with data-confirm
  document.addEventListener('click', function(e) {
    var btn = e.target.closest('[data-confirm]');
    if (btn) {
      e.preventDefault();
      window.confirmAction(btn.getAttribute('data-confirm'), function() {
        if (btn.tagName === 'A') window.location.href = btn.href;
        else if (btn.tagName === 'BUTTON' || btn.tagName === 'INPUT') {
          var form = btn.closest('form');
          if (form) form.submit();
        }
      });
    }
  });

  // Auto-refresh submission status (used on business detail page)
  window.startSubmissionPolling = function(businessId, interval) {
    interval = interval || 30000;
    setInterval(function() {
      api.get('/api/submissions/' + businessId).then(function(data) {
        updateSubmissionTable(data.submissions);
        updateProgressBar(data);
      });
    }, interval);
  };

  function updateSubmissionTable(submissions) {
    var tbody = document.querySelector('#submissions-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!submissions || submissions.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-center py-8 text-gray-500">No submissions yet</td></tr>';
      return;
    }
    submissions.forEach(function(s) {
      var tr = document.createElement('tr');
      tr.innerHTML = '<td>' + escHtml(s.directory_name) + '</td>' +
        '<td><span class="badge badge-' + statusClass(s.status) + '">' + escHtml(s.status) + '</span></td>' +
        '<td>' + (s.error_message ? '<span class="text-red-400 text-sm">' + escHtml(s.error_message) + '</span>' : '-') + '</td>' +
        '<td class="text-sm text-gray-400">' + (s.submitted_at || '-') + '</td>';
      tbody.appendChild(tr);
    });
  }

  function updateProgressBar(data) {
    var bar = document.querySelector('#progress-fill');
    if (!bar) return;
    var pct = data.completion_pct || 0;
    bar.style.width = pct + '%';
    bar.textContent = pct + '%';
  }

  function statusClass(status) {
    return { pending: 'pending', in_progress: 'in-progress', completed: 'completed', failed: 'failed', skipped: 'skipped' }[status] || 'gray';
  }

  function escHtml(str) {
    if (!str) return '';
    var d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  // Search debounce
  window.debounce = function(fn, delay) {
    var timer;
    return function() {
      var args = arguments, ctx = this;
      clearTimeout(timer);
      timer = setTimeout(function() { fn.apply(ctx, args); }, delay || 300);
    };
  };

  // Form validation
  document.addEventListener('submit', function(e) {
    var form = e.target;
    if (form.classList.contains('needs-validation')) {
      var required = form.querySelectorAll('[required]');
      var valid = true;
      required.forEach(function(field) {
        if (!field.value.trim()) {
          field.classList.add('is-invalid');
          valid = false;
        } else {
          field.classList.remove('is-invalid');
        }
      });
      if (!valid) e.preventDefault();
    }
  });

  // Mobile sidebar toggle
  var sidebarToggle = document.getElementById('sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      document.querySelector('.sidebar').classList.toggle('open');
    });
  }

})();
