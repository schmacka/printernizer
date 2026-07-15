# Mobile Image Preview Implementation Plan

## Current Issue
The rotating 3D model preview in the library file cards only works with mouse hover events (`mouseenter`/`mouseleave`), which do not work on mobile/touch devices.

## Affected Code
- **File**: `frontend/js/library.js`
- **Method**: `setupAnimatedThumbnail()` (lines 315-400)
- **Current Events**: `mouseenter`, `mouseleave`

## Implementation Plan

### Option 1: Single Tap Toggle (Recommended)
**User Experience**: Tap once to show animation, tap again to hide
**Pros**: Simple, intuitive, works well on mobile
**Cons**: Requires two taps to close

**Implementation**:
1. Add touch event listeners alongside mouse events
2. Track animation state (static/animated)
3. Toggle between states on tap
4. Ensure mouse and touch events don't conflict

### Option 2: Tap to Show, Tap Outside to Hide
**User Experience**: Tap image to animate, tap anywhere else to return to static
**Pros**: More natural "preview" behavior
**Cons**: Slightly more complex implementation

**Implementation**:
1. Add touch event listener to thumbnail
2. Add document-level touch listener to detect outside taps
3. Manage active state tracking
4. Clean up listeners when switching between files

### Option 3: Long Press to Show
**User Experience**: Long press (500ms+) to show animation, release to hide
**Pros**: Doesn't interfere with card click behavior
**Cons**: Less discoverable, requires user education

**Implementation**:
1. Add `touchstart` event with timer
2. Add `touchend` and `touchcancel` to clear timer
3. Show animation after threshold
4. Hide on touch end

## Recommended Approach: Hybrid (Option 1 + Mouse Events)

### Technical Implementation

#### 1. Update `setupAnimatedThumbnail()` Method

```javascript
setupAnimatedThumbnail(thumbnailElement) {
    const img = thumbnailElement.querySelector('.thumbnail-image');
    const staticUrl = thumbnailElement.dataset.staticUrl;
    const animatedUrl = thumbnailElement.dataset.animatedUrl;

    if (!img || !animatedUrl) {
        return;
    }

    let isAnimatedLoaded = false;
    let isHovering = false;
    let isAnimating = false; // NEW: Track animation state for touch
    let loadTimeout = null;

    const preloadAnimatedGif = () => {
        if (isAnimatedLoaded) return;

        const preloadImg = new Image();
        preloadImg.onload = () => {
            isAnimatedLoaded = true;
            if ((isHovering || isAnimating) && img.src !== animatedUrl) {
                img.src = animatedUrl;
            }
        };
        preloadImg.onerror = (error) => {
            Logger.error('Failed to load animated preview', { url: animatedUrl, error });
        };
        preloadImg.src = animatedUrl;
    };

    // MOUSE EVENTS (Desktop)
    thumbnailElement.addEventListener('mouseenter', () => {
        isHovering = true;
        loadTimeout = setTimeout(() => {
            if (isHovering) {
                preloadAnimatedGif();
                if (isAnimatedLoaded && img.src !== animatedUrl) {
                    img.src = animatedUrl;
                }
            }
        }, 200);
    });

    thumbnailElement.addEventListener('mouseleave', () => {
        isHovering = false;
        if (loadTimeout) {
            clearTimeout(loadTimeout);
            loadTimeout = null;
        }
        if (img.src !== staticUrl) {
            img.src = staticUrl;
        }
    });

    // TOUCH EVENTS (Mobile)
    thumbnailElement.addEventListener('touchstart', (e) => {
        // Prevent this from triggering mouseenter
        e.stopPropagation();

        // Toggle animation state
        isAnimating = !isAnimating;

        if (isAnimating) {
            // Show animation
            preloadAnimatedGif();
            if (isAnimatedLoaded && img.src !== animatedUrl) {
                img.src = animatedUrl;
            }
            // Add visual indicator
            thumbnailElement.classList.add('animating');
        } else {
            // Return to static
            if (img.src !== staticUrl) {
                img.src = staticUrl;
            }
            thumbnailElement.classList.remove('animating');
        }
    }, { passive: true });
}
```

#### 2. Add CSS for Visual Feedback

Add to `frontend/css/library.css` or main CSS file:

```css
/* Visual indicator for animated state on mobile */
.file-card-thumbnail.animating::after {
    content: '🔄';
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    pointer-events: none;
}

/* Ensure touch targets are large enough (44x44px minimum) */
.file-card-thumbnail {
    min-height: 44px;
    min-width: 44px;
}
```

#### 3. Prevent Conflicts with Card Click

Update the card click handler in `renderFiles()` to not trigger when tapping the thumbnail:

```javascript
grid.querySelectorAll('.library-file-card').forEach(card => {
    card.addEventListener('click', (e) => {
        // Don't open modal if clicking thumbnail on touch device
        if (e.target.closest('.file-card-thumbnail') && 'ontouchstart' in window) {
            return;
        }

        const checksum = card.dataset.checksum;
        const file = files.find(f => f.checksum === checksum);
        if (file) this.showFileDetail(file);
    });
});
```

## Testing Checklist

### Desktop Testing
- [ ] Mouse hover shows animation
- [ ] Mouse leave returns to static
- [ ] Animation preloads on first hover
- [ ] No console errors
- [ ] Click still opens detail modal

### Mobile Testing (iOS Safari, Chrome Mobile, Firefox Mobile)
- [ ] Tap toggles animation on/off
- [ ] Visual indicator appears when animating
- [ ] No interference with card click/tap
- [ ] No unwanted scrolling when tapping
- [ ] Animation state resets when scrolling away
- [ ] Works on both small and large touch targets

### Edge Cases
- [ ] Rapid tapping doesn't break state
- [ ] Works with multiple cards
- [ ] State resets when navigating away
- [ ] Memory cleanup on page unload
- [ ] Works with drag-and-drop
- [ ] Animation loads correctly on slow connections

## Alternative: Modal-Only Animation

If the above approach is too complex, consider only showing animated previews in the **detail modal** where there's more screen space:

1. Remove animation from grid cards entirely
2. Add animated preview to file detail modal
3. Use full-size animated GIF with better quality
4. Add touch controls (swipe left/right for rotation speed?)

## Files to Modify

1. **`frontend/js/library.js`**
   - Update `setupAnimatedThumbnail()` method
   - Update card click handler in `renderFiles()`

2. **`frontend/css/library.css`** (or main stylesheet)
   - Add `.animating` state styles
   - Ensure touch target sizes

3. **Testing**
   - Test on iOS Safari (most restrictive)
   - Test on Android Chrome
   - Test on various screen sizes

## Accessibility Considerations

- Add ARIA labels for screen readers
- Ensure animation can be stopped (WCAG 2.2.2)
- Provide alternative preview method for reduced-motion preference
- Consider adding `prefers-reduced-motion` CSS query

```css
@media (prefers-reduced-motion: reduce) {
    .file-card-thumbnail.animating img {
        animation: none !important;
    }
}
```

## Future Enhancements

1. **Gesture support**: Swipe to rotate manually
2. **Speed control**: Tap and hold to slow down rotation
3. **Full-screen preview**: Double-tap for fullscreen 3D view
4. **Auto-rotation**: Optional auto-rotate in detail modal
5. **WebGL preview**: Real-time 3D preview using Three.js

## Performance Notes

- Animated GIFs can be large (>500KB)
- Consider lazy loading for off-screen cards
- Add loading indicator while GIF loads
- Cache loaded GIFs in memory
- Clear cache when memory pressure is high

## Branch and Commit Strategy

1. Create feature branch: `claude/mobile-image-preview-[session-id]`
2. Commit changes with message: `feat: Add mobile touch support for animated image previews`
3. Test thoroughly on mobile devices
4. Push and create PR to `development` branch
5. Document in CHANGELOG.md under "Added" section
