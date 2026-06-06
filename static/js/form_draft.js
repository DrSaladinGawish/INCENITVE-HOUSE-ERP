/* Phase 4: Form Polish - Auto-save draft, unsaved changes warning, validation */

(function() {
    'use strict';

    function getFormId(form) {
        var path = window.location.pathname.replace(/\//g, '_');
        var id = form.getAttribute('data-record-id') || 'new';
        return 'draft' + path + '_' + id;
    }

    function serializeForm(form) {
        var data = {};
        var formData = new FormData(form);
        formData.forEach(function(value, key) {
            if (data[key] !== undefined) {
                if (!Array.isArray(data[key])) data[key] = [data[key]];
                data[key].push(value);
            } else {
                data[key] = value;
            }
        });
        return data;
    }

    function deserializeForm(form, data) {
        for (var key in data) {
            if (data.hasOwnProperty(key)) {
                var el = form.querySelector('[name="' + key + '"]');
                if (el) {
                    if (el.type === 'checkbox') el.checked = data[key] === 'on' || data[key] === true;
                    else el.value = data[key];
                }
            }
        }
    }

    function restoreDraft(form) {
        var key = getFormId(form);
        try {
            var raw = localStorage.getItem(key);
            if (raw) {
                var data = JSON.parse(raw);
                deserializeForm(form, data);
                var banner = document.createElement('div');
                banner.className = 'alert alert-info';
                banner.style.cssText = 'padding:10px 15px;margin-bottom:10px;border-radius:4px;background:#e3f2fd;color:#1565c0;display:flex;justify-content:space-between;align-items:center';
                banner.innerHTML = '<span>Draft restored from ' + (new Date(data._saved_at || Date.now())).toLocaleString() + '</span>' +
                    '<span><button class="btn btn-sm btn-primary" onclick="this.parentElement.parentElement.remove()">Dismiss</button> ' +
                    '<button class="btn btn-sm btn-outline" onclick="clearDraft(\'' + key + '\');this.parentElement.parentElement.remove()">Discard Draft</button></span>';
                form.parentElement.insertBefore(banner, form);
            }
        } catch(e) {}
    }

    function autoSaveDraft(form) {
        var key = getFormId(form);
        try {
            var data = serializeForm(form);
            data._saved_at = Date.now();
            data._url = window.location.href;
            localStorage.setItem(key, JSON.stringify(data));
        } catch(e) {}
    }

    function clearDraft(key) {
        try { localStorage.removeItem(key); } catch(e) {}
    }

    function clearDraftOnSubmit(form) {
        form.addEventListener('submit', function() {
            clearDraft(getFormId(form));
        });
    }

    function initDirtyTracking(form) {
        var dirty = false;
        form.addEventListener('change', function() { dirty = true; });
        form.addEventListener('input', function() { dirty = true; });
        window.addEventListener('beforeunload', function(e) {
            if (dirty) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            }
        });
        // Sidebar links
        document.querySelectorAll('nav a, .sidebar a').forEach(function(a) {
            a.addEventListener('click', function(e) {
                if (dirty && !confirm('You have unsaved changes. Leave without saving?')) {
                    e.preventDefault();
                }
            });
        });
    }

    function initInlineValidation(form) {
        form.querySelectorAll('[required]').forEach(function(el) {
            el.addEventListener('blur', function() {
                if (!el.value.trim()) {
                    el.style.borderColor = '#e53935';
                    var err = el.nextElementSibling;
                    if (!err || !err.classList.contains('field-error')) {
                        err = document.createElement('div');
                        err.className = 'field-error';
                        err.style.cssText = 'color:#e53935;font-size:12px;margin-top:2px';
                        el.parentElement.appendChild(err);
                    }
                    err.textContent = 'This field is required';
                } else {
                    el.style.borderColor = '';
                    var err = el.nextElementSibling;
                    if (err && err.classList.contains('field-error')) err.remove();
                }
            });
        });
    }

    // Initialize on all forms with data-draft attribute
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('form[data-draft]').forEach(function(form) {
            restoreDraft(form);
            clearDraftOnSubmit(form);
            initDirtyTracking(form);
            initInlineValidation(form);
            setInterval(function() { autoSaveDraft(form); }, 30000);
        });
    });

    window.clearDraft = clearDraft;
})();
