/**
 * dashboard.js — Sidebar nav + flipped tabs + paint timing
 * v9.0 — Final architecture: sidebar with module windows and 3 flipped tabs
 */

console.time('dashboard_paint')

document.addEventListener('DOMContentLoaded', function () {
  /* ===================================================================
   * 1. Sidebar Navigation — Click module to switch view
   * =================================================================== */
  var menuItems = document.querySelectorAll('.ih-menu-item')
  var moduleSections = document.querySelectorAll('.ih-module-section')

  menuItems.forEach(function (item) {
    item.addEventListener('click', function (e) {
      var module = item.getAttribute('data-module')
      if (!module) return
      e.preventDefault()

      // Update sidebar active state
      menuItems.forEach(function (mi) {
        var label = mi.querySelector('.ih-menu-label')
        if (label) label.classList.remove('ih-active')
      })
      var activeLabel = item.querySelector('.ih-menu-label')
      if (activeLabel) activeLabel.classList.add('ih-active')

      // Show selected module, hide others
      moduleSections.forEach(function (section) {
        section.classList.remove('ih-module-active')
      })
      var target = document.getElementById('module-' + module)
      if (target) {
        target.classList.add('ih-module-active')
        // Close all flip panels when switching modules
        var openPanels = target.querySelectorAll('.ih-flip-panel.ih-panel-open')
        openPanels.forEach(function (p) { p.classList.remove('ih-panel-open') })
        var activeTabs = target.querySelectorAll('.ih-flip-tab.ih-tab-active')
        activeTabs.forEach(function (t) { t.classList.remove('ih-tab-active') })
      }
    })
  })

  /* ===================================================================
   * 2. Flipped Tabs — Click to flip open/close
   * =================================================================== */
  var flipTabs = document.querySelectorAll('.ih-flip-tab')

  flipTabs.forEach(function (tab) {
    tab.addEventListener('click', function (e) {
      e.stopPropagation()
      var panelId = tab.getAttribute('data-tab')
      if (!panelId) return

      var panel = document.getElementById(panelId)
      if (!panel) return

      var isOpen = panel.classList.contains('ih-panel-open')

      // Find the parent module section
      var moduleSection = tab.closest('.ih-module-section')

      // Close all other tabs/panels in this module section
      if (moduleSection) {
        var siblingTabs = moduleSection.querySelectorAll('.ih-flip-tab.ih-tab-active')
        siblingTabs.forEach(function (st) {
          if (st !== tab) {
            st.classList.remove('ih-tab-active')
            var sid = st.getAttribute('data-tab')
            var sp = document.getElementById(sid)
            if (sp) sp.classList.remove('ih-panel-open')
          }
        })
      }

      // Toggle current tab
      if (isOpen) {
        panel.classList.remove('ih-panel-open')
        tab.classList.remove('ih-tab-active')
      } else {
        panel.classList.add('ih-panel-open')
        tab.classList.add('ih-tab-active')
      }
    })
  })

  /* ===================================================================
   * 3. Click Outside — Close all flipped tabs
   * =================================================================== */
  document.addEventListener('click', function () {
    var openTabs = document.querySelectorAll('.ih-flip-tab.ih-tab-active')
    openTabs.forEach(function (tab) {
      tab.classList.remove('ih-tab-active')
      var panelId = tab.getAttribute('data-tab')
      var panel = document.getElementById(panelId)
      if (panel) panel.classList.remove('ih-panel-open')
    })
  })

  // Prevent click inside panel from bubbling
  var panels = document.querySelectorAll('.ih-flip-panel')
  panels.forEach(function (p) {
    p.addEventListener('click', function (e) {
      e.stopPropagation()
    })
  })

  /* ===================================================================
   * Paint Timing
   * =================================================================== */
  console.timeEnd('dashboard_paint')
})
