/* ========== Tab Switching Logic ========== */
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      this.classList.add('active');
      var tabId = this.dataset.tab;
      if (tabId) {
        document.getElementById('tab-' + tabId).classList.add('active');
      }
    });
  });

  /* ========== Mobile Search Overlay ========== */
  // Inject search overlay HTML if not present
  if (!document.getElementById('mobile-search-overlay')) {
    var overlayDiv = document.createElement('div');
    overlayDiv.id = 'mobile-search-overlay';
    overlayDiv.className = 'mobile-search-overlay';
    overlayDiv.innerHTML =
      '<div class="ms-bar">' +
        '<input type="text" id="ms-input" placeholder="Search articles..." autocomplete="off">' +
        '<button class="ms-close" id="ms-close">✕</button>' +
      '</div>';
    document.body.appendChild(overlayDiv);
  }

  var searchIcon = document.querySelector('.search-icon');
  var msOverlay = document.getElementById('mobile-search-overlay');
  var msInput = document.getElementById('ms-input');
  var msClose = document.getElementById('ms-close');

  if (searchIcon && msOverlay) {
    // Open overlay
    searchIcon.addEventListener('click', function(e) {
      if (window.innerWidth <= 768) {
        e.stopPropagation();
        msOverlay.classList.add('open');
        setTimeout(function() { msInput.focus(); }, 100);
      }
    });

    // Close on ✕
    msClose.addEventListener('click', function() {
      msOverlay.classList.remove('open');
    });

    // Close on Escape
    msInput.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        msOverlay.classList.remove('open');
        msInput.blur();
      }
    });

    // Close on tap outside overlay
    document.addEventListener('click', function(e) {
      if (msOverlay.classList.contains('open') && !e.target.closest('.mobile-search-overlay') && !e.target.closest('.search-icon')) {
        msOverlay.classList.remove('open');
      }
    });
  }
});
