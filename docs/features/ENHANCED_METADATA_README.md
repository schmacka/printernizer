# Enhanced 3D Model Metadata Display

## Quick Start Guide

### For Users

When viewing 3D files in Printernizer, you'll now see comprehensive metadata including:

📐 **Dimensions** - Physical size of your model  
💰 **Cost** - Estimated material and energy costs  
⭐ **Quality** - Complexity score and success probability  
🧩 **Objects** - Number of parts in the model  
⚙️ **Settings** - Layer height, infill, temperatures  
🧵 **Materials** - Filament weight, colors, types  
🖨️ **Compatibility** - Which printers can print this file  

### How to Use

1. Navigate to the **Files** page
2. Click on any 3D file (3MF, STL, G-code)
3. The preview modal opens with basic info
4. Enhanced metadata loads automatically below
5. Scroll through all the detailed information
6. Use this data to make informed printing decisions

## For Developers

### Component Architecture

```
EnhancedFileMetadata (Class)
├── loadMetadata() - Async API loading with caching
├── render() - Main rendering orchestrator
├── renderSummaryCards() - Top-level overview cards
├── renderDetailedSections() - Comprehensive info sections
│   ├── renderPhysicalProperties()
│   ├── renderPrintSettings()
│   ├── renderMaterialRequirements()
│   ├── renderCostBreakdown()
│   ├── renderQualityMetrics()
│   └── renderCompatibilityInfo()
└── Loading/Error/Empty states
```

### API Integration

**Endpoint:** `GET /api/v1/files/{file_id}/metadata/enhanced`

**Query Parameters:**
- `force_refresh` (boolean): Bypass cache and re-analyze file

**Response:** JSON with nested metadata objects

### Usage Example

```javascript
// Create metadata instance
const metadata = new EnhancedFileMetadata(fileId);

// Load metadata from API
await metadata.loadMetadata();

// Render to DOM
document.getElementById('container').innerHTML = metadata.render();

// Force refresh (bypass cache)
await metadata.loadMetadata(true);

// Clear cache for this file
metadata.clearCache();

// Clear all cached metadata
EnhancedFileMetadata.clearAllCache();
```

### Styling

All styles are in `frontend/css/enhanced-metadata.css`

**Key CSS Variables:**
```css
--bg-primary: Background for cards
--bg-secondary: Background for sections
--border-color: Border colors
--text-primary: Primary text color
--text-secondary: Secondary text color
```

**Responsive Breakpoints:**
- Desktop: >1024px
- Tablet: 768-1024px
- Mobile: <768px
- Small Mobile: <480px

### Customization

#### Adding New Metadata Fields

1. Add field to backend `EnhancedFileMetadata` model
2. Extract value in `BambuParser` or `ThreeMFAnalyzer`
3. Add rendering logic in `enhanced-metadata.js`
4. Style in `enhanced-metadata.css`

#### Changing Styles

All component styles are namespaced with `.metadata-*` classes.

Example:
```css
.metadata-summary-cards {
    /* Customize grid layout */
}

.summary-card {
    /* Customize card appearance */
}
```

#### Supporting New File Types

Metadata extraction happens in Phase 1 (backend).

For frontend display:
1. Check `file_type` in `render3DFilePreview()`
2. Add file extension to `is3DFile` check
3. Metadata will automatically display if available

## File Structure

```
frontend/
├── css/
│   ├── enhanced-metadata.css     # All metadata styles
│   └── components.css            # Container styles
├── js/
│   ├── enhanced-metadata.js      # Metadata component
│   └── files.js                  # Integration point
└── index.html                    # Includes CSS & JS

docs/features/
└── ENHANCED_METADATA_PHASE2_IMPLEMENTATION.md

src/api/routers/
└── health.py                     # Version updated to 1.2.0
```

## Testing

### Manual Testing

1. Run integration verification:
   ```bash
   python3 verify_phase2_integration.py
   ```

2. Open test page:
   ```bash
   # Start a local server
   cd /tmp
   python3 -m http.server 8080
   # Open browser to http://localhost:8080/test-enhanced-metadata.html
   ```

3. Test in application:
   ```bash
   ./run.sh
   # Open http://localhost:8000
   # Navigate to Files → Click 3D file
   ```

### Browser Testing

Test in multiple browsers:
- Chrome (recommended)
- Firefox
- Safari
- Edge

Test responsive design:
- Desktop (1920x1080)
- Tablet (768x1024)
- Mobile (375x667)

## Troubleshooting

### Metadata Not Loading

**Symptom:** Loading spinner never completes

**Solutions:**
1. Check browser console for errors
2. Verify API endpoint is accessible: `/api/v1/files/{id}/metadata/enhanced`
3. Ensure Phase 1 backend is implemented
4. Check file has been analyzed (backend extraction)

### Styles Not Applied

**Symptom:** Plain unstyled HTML

**Solutions:**
1. Verify `enhanced-metadata.css` is loaded in browser dev tools
2. Check CSS path in `index.html`
3. Clear browser cache
4. Check for CSS conflicts with existing styles

### Display Issues on Mobile

**Symptom:** Layout broken on small screens

**Solutions:**
1. Test with actual mobile device (not just browser resize)
2. Check viewport meta tag in HTML
3. Verify responsive breakpoints in CSS
4. Test with mobile browser dev tools

### Empty State Always Shows

**Symptom:** "Keine erweiterten Metadaten verfügbar"

**Solutions:**
1. File may not have metadata yet - try forcing refresh
2. Backend extraction may have failed - check backend logs
3. Metadata may be in old format - re-analyze file
4. Check if file type is supported (3MF, G-code, STL)

## Performance Considerations

### Caching Strategy

- **In-memory cache:** 5-minute TTL per file
- **No persistent storage:** Cache clears on page reload
- **Manual refresh:** Use `force_refresh=true` query param

### Optimization Tips

1. **Lazy load:** Metadata loads only when preview opens
2. **Async rendering:** Non-blocking UI updates
3. **Efficient DOM:** Minimal reflows and repaints
4. **CSS transforms:** Hardware-accelerated animations

### Load Times

Typical metadata load times:
- **Cache hit:** <10ms
- **API call:** 50-200ms
- **File analysis:** 1-3 seconds (first time)

## Accessibility

### WCAG 2.1 AA Compliance

✅ Color contrast ratios meet standards  
✅ Semantic HTML structure  
✅ ARIA labels for screen readers  
✅ Keyboard navigation support  
✅ Text scaling support  

### Screen Reader Support

All sections have proper labels:
- `aria-label` on interactive elements
- Semantic headings (h1-h4)
- Proper list structures
- Descriptive icon labels

## Browser Support

| Browser | Version | Status |
|---------|---------|--------|
| Chrome  | 90+     | ✅ Full support |
| Firefox | 88+     | ✅ Full support |
| Safari  | 14+     | ✅ Full support |
| Edge    | 90+     | ✅ Full support |
| IE 11   | -       | ❌ Not supported |

**Required Features:**
- ES6+ JavaScript
- CSS Grid
- Flexbox
- Async/Await
- Fetch API

## Future Roadmap

See Issue #43 for Phase 3 plans:
- Quality assessment with success prediction
- Cost optimization recommendations
- Printer compatibility matching
- Smart print setting suggestions

## Contributing

When adding features to this component:

1. Maintain responsive design
2. Follow existing code style
3. Add appropriate error handling
4. Update documentation
5. Test across browsers
6. Verify accessibility

## License

Part of Printernizer project - see main LICENSE file

## Support

- GitHub Issues: [schmacka/printernizer/issues](https://github.com/schmacka/printernizer/issues)
- Main Issue: #43
- Phase 2 Issue: #45

---

**Version:** 1.2.0  
**Status:** ✅ Production Ready  
**Last Updated:** 2025-10-02
