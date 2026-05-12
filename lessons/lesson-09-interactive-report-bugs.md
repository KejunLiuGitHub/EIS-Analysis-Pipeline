# Lesson 9: Interactive Report Bug Fixes

## Context

The multi-sample interactive report (`reports/eis_report.html`) had a critical bug: **sample cards in the sidebar did not respond to clicks**. The root cause was not a single error but a chain of interacting JS defects. Fixing it required a complete rewrite of `template.html`.

---

## Bug 1: IIFE Crash Kills All Event Listeners

### Problem

The entire script was wrapped in an IIFE:

```javascript
(function(){
  var R = JSON.parse(...);
  // ... buildSidebar(), selectSample(), etc.
  buildSidebar();
})();
```

If **any** error occurs inside the IIFE (e.g. `undefined.toFixed()`), the whole function aborts. Event listeners attached inside are never registered. The page looks loaded, but nothing is clickable.

### Evidence

No console errors appear on initial load because the crash happens before `addEventListener` calls. The user sees rendered sidebar cards but clicking them does nothing.

### Solution

Replace IIFE with `DOMContentLoaded` + top-level functions. Wrap each major function body in `try/catch`:

```javascript
document.addEventListener('DOMContentLoaded', function() {
  var R = JSON.parse(document.getElementById('eis-data').textContent);
  // ...
  
  function buildSidebar() {
    try {
      // ... original logic
    } catch(e) {
      console.error('buildSidebar error:', e);
      showError('Sidebar error: ' + e.message);
    }
  }
  
  try {
    buildSidebar();
    if (first) selectSample(first);
  } catch(e) {
    console.error('Init error:', e);
    showError('Initialization error: ' + e.message);
  }
});
```

Add a `showError()` helper that renders a red banner in the plot container instead of leaving it blank:

```javascript
function showError(msg) {
  document.getElementById('plot-container').innerHTML =
    '<div style="color:#c62828;background:#ffe8e8;padding:1rem;border-radius:4px;margin:1rem 0">' +
    '<strong>Error:</strong> ' + msg + '</div>';
}
```

---

## Bug 2: `.toFixed()` / `.toExponential()` on `undefined`

### Problem

Code like `rt.sigma_S_cm.toExponential(2)` or `af.Ea_eV.toFixed(3)` throws if the field is missing. In the IIFE world, this single throw kills the entire script.

### Solution

Never call formatting methods on raw data. Use safe wrappers:

```javascript
function fmt(v, d) {
  return (typeof v === 'number' && !isNaN(v)) ? v.toFixed(d) : '?';
}
function fmtExp(v) {
  return (typeof v === 'number' && !isNaN(v)) ? v.toExponential(2) : '?';
}
```

Replace **every** `.toFixed()` and `.toExponential()` in the file with these helpers. This includes:
- Sidebar sigma display
- Parameter bar (R₀, R₁, R₂, σ, χ²/N, fc)
- Plot annotations (ZC, DC resistance)
- Hover text formatting
- Arrhenius fit labels

---

## Bug 3: `Plotly.react()` Fails on Empty Container

### Problem

`Plotly.react('plot-container', traces, layout)` only works if the container **already contains a Plotly chart**. If the container was previously set to plain HTML (e.g. `<div class="loading">Fit failed...</div>`), `react` does nothing — the chart never appears.

### Evidence

Clicking a sample with converged fit after viewing a "Fit failed" sample leaves the plot container empty. No console error, just blank space.

### Solution

Create a `renderPlot()` helper that detects whether Plotly already exists in the container:

```javascript
function renderPlot(containerId, traces, layout) {
  var c = document.getElementById(containerId);
  if (c.querySelector('.plotly')) {
    Plotly.react(containerId, traces, layout);
  } else {
    Plotly.newPlot(containerId, traces, layout);
  }
}
```

Also clear the container **before** calling renderPlot in `updatePlot()`:

```javascript
function updatePlot() {
  var d = getData(), c = document.getElementById('plot-container');
  if (!d.fit.converged) {
    c.innerHTML = '<div class="loading">Fit failed: ' + (d.fit.error || 'unknown') + '</div>';
    return;
  }
  c.innerHTML = '';  // ← critical: remove stale DOM
  if (curTab === 'nyquist') renderNyquist(d);
  // ...
}
```

---

## Bug 4: JSON Field Name Mismatch (Python ↔ JS)

### Problem

Python generated `arrhenius.ln_sigma0`, but JavaScript expected `af.intercept`:

```javascript
// WRONG — field does not exist in JSON
var yf = xf.map(function(xv) { return af.slope * xv + af.intercept; });
```

This produced `NaN` for every fit-line point. Plotly SVG renderer then threw 80+ errors like `rotate(0,403.93,NaN)` and the chart either failed to render or was invisible.

### Solution

Always verify field names match between Python `json.dumps()` and JS `JSON.parse()`:

```javascript
// CORRECT — matches Python output
var yf = xf.map(function(xv) { return af.slope * xv + af.ln_sigma0; });
```

Rule: when passing data across Python→JS boundary, print/sample the JSON keys on both sides.

---

## Bug 5: AE Cards Missing `data-sample`

### Problem

Activation Energy list cards were created without `data-sample`:

```javascript
var card = document.createElement('div');
card.className = 'sample-card';
// missing: card.dataset.sample = sid;
```

`selectSample()` used `document.querySelector('.sample-card[data-sample="'+sid+'"]')` to highlight the active card. Since AE cards had no `data-sample`, they could never be highlighted.

### Solution

Add `data-sample` to every card, and use `querySelectorAll` so both the sample-list card and AE-list card get the `.active` class:

```javascript
// In buildSidebar() for AE cards
card.dataset.sample = sid;

// In selectSample()
document.querySelectorAll('.sample-card[data-sample="'+sid+'"]')
  .forEach(function(c) { c.classList.add('active'); });
```

---

## Summary Checklist

When building a Plotly-based interactive report with inline JSON:

- [ ] Replace IIFE with `DOMContentLoaded`
- [ ] Wrap every `render*` function in `try/catch`
- [ ] Add `fmt()` / `fmtExp()` wrappers for all number formatting
- [ ] Use `renderPlot()` helper (newPlot ↔ react) instead of raw `Plotly.react`
- [ ] Clear `plot-container` with `innerHTML = ''` before drawing
- [ ] Verify JSON field names match between Python and JS
- [ ] Add `data-*` attributes to all dynamically created clickable elements
- [ ] Open browser DevTools and test clicking every element before declaring done
