---
name: LinearMouseSim Racing
colors:
  surface: "#0a0a14"
  surface-dim: "#0f0f1a"
  surface-bright: "#2a2a4a"
  surface-container-lowest: "#06060d"
  surface-container-low: "#121224"
  surface-container: "#16162a"
  surface-container-high: "#1a1a3e"
  surface-container-highest: "#22224e"
  on-surface: "#ffffff"
  on-surface-variant: "#8888aa"
  inverse-surface: "#ffffff"
  inverse-on-surface: "#0a0a14"
  outline: "#3a3a6a"
  outline-variant: "#2a2a4a"
  surface-tint: "#e94560"
  primary: "#e94560"
  on-primary: "#ffffff"
  primary-container: "#2a1018"
  on-primary-container: "#ff8899"
  inverse-primary: "#ff6b85"
  secondary: "#4a90d9"
  on-secondary: "#ffffff"
  secondary-container: "#102a4a"
  on-secondary-container: "#7ab8ff"
  tertiary: "#00ff88"
  on-tertiary: "#00331a"
  tertiary-container: "#002210"
  on-tertiary-container: "#66ffaa"
  error: "#ff4444"
  on-error: "#ffffff"
  error-container: "#2a0a0a"
  on-error-container: "#ff8888"
  warning: "#ffaa00"
  on-warning: "#332200"
  warning-container: "#2a1a00"
  on-warning-container: "#ffcc44"
  background: "#0a0a14"
  on-background: "#ffffff"
  surface-variant: "#2a2a4a"
typography:
  display-lg:
    fontFamily: "Segoe UI"
    fontSize: 48px
    fontWeight: "700"
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: "Segoe UI"
    fontSize: 24px
    fontWeight: "700"
    lineHeight: 32px
  headline-md:
    fontFamily: "Segoe UI"
    fontSize: 20px
    fontWeight: "600"
    lineHeight: 28px
  body-lg:
    fontFamily: "Segoe UI"
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 24px
  body-md:
    fontFamily: "Segoe UI"
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 20px
  body-sm:
    fontFamily: "Segoe UI"
    fontSize: 12px
    fontWeight: "400"
    lineHeight: 16px
  label-sm:
    fontFamily: "Segoe UI"
    fontSize: 11px
    fontWeight: "600"
    lineHeight: 16px
    letterSpacing: 0.05em
  value-lg:
    fontFamily: "Consolas"
    fontSize: 28px
    fontWeight: "700"
    lineHeight: 36px
  value-md:
    fontFamily: "Consolas"
    fontSize: 18px
    fontWeight: "700"
    lineHeight: 24px
  value-sm:
    fontFamily: "Consolas"
    fontSize: 14px
    fontWeight: "600"
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 16px
  card-gap: 12px
  section-margin: 24px
  panel-padding: 16px
components:
  panel-standard:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline}"
    rounded: "{rounded.lg}"
    padding: "{spacing.panel-padding}"
  panel-dark:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline-variant}"
    rounded: "{rounded.md}"
    padding: "{spacing.panel-padding}"
  card-standard:
    backgroundColor: "{colors.surface-container-high}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline}"
    rounded: "{rounded.md}"
    padding: "{spacing.card-gap}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.md}"
    height: 36px
    padding: 0 16px
  button-secondary:
    backgroundColor: "{colors.surface-container-high}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.md}"
    height: 36px
    padding: 0 16px
  button-toggle:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface-variant}"
    borderColor: "{colors.outline-variant}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.sm}"
    height: 32px
    padding: 0 12px
  button-toggle-active:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.on-secondary}"
    borderColor: "{colors.secondary}"
  slider-track:
    backgroundColor: "{colors.surface-container-low}"
    borderColor: "{colors.outline-variant}"
    rounded: "{rounded.full}"
    height: 6px
  slider-thumb:
    backgroundColor: "{colors.secondary}"
    borderColor: "{colors.on-secondary}"
    rounded: "{rounded.full}"
    size: 16px
  input-field:
    backgroundColor: "{colors.surface-container-high}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline}"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: 8px 12px
    height: 36px
  input-field-focused:
    borderColor: "{colors.secondary}"
  dropdown-select:
    backgroundColor: "{colors.surface-container-high}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline}"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: 8px 12px
    height: 36px
  status-indicator-active:
    backgroundColor: "{colors.tertiary}"
    glowColor: "{colors.tertiary}"
    size: 12px
  status-indicator-inactive:
    backgroundColor: "{colors.error}"
    glowColor: "{colors.error}"
    size: 12px
  status-indicator-warning:
    backgroundColor: "{colors.warning}"
    glowColor: "{colors.warning}"
    size: 12px
  heading-section:
    textColor: "{colors.on-surface}"
    typography: "{typography.headline-md}"
    paddingBottom: "{spacing.card-gap}"
    borderBottom: "{colors.outline-variant}"
  label-field:
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.label-sm}"
    textTransform: "uppercase"
  value-display:
    textColor: "{colors.on-surface}"
    typography: "{typography.value-md}"
  steering-wheel-base:
    backgroundColor: "{colors.surface-container-lowest}"
    borderColor: "{colors.outline-variant}"
    rounded: "{rounded.full}"
  steering-wheel-rim:
    backgroundColor: "{colors.surface-container-highest}"
    borderColor: "{colors.outline}"
  steering-wheel-accent:
    backgroundColor: "{colors.primary}"
---

## Brand & Style

LinearMouseSim Racing features a dark, premium racing simulator aesthetic designed to evoke speed, precision, and technical excellence. The design emphasizes:

- Deep space-inspired color palette with high contrast
- Racing-themed accent colors (red, blue, green)
- Clean, modern typography with Segoe UI for interface and Consolas for technical values
- Smooth rounded corners and subtle borders
- Real-time feedback and animation

## Colors

The palette is rooted in deep space tones with racing-inspired accents:

- **Surface (#0a0a14):** Deep black-blue for main backgrounds
- **Surface Container (#16162a):** Dark panel backgrounds
- **Surface Container High (#1a1a3e):** Cards and interactive elements
- **Primary (#e94560):** Racing red - the primary action color
- **Secondary (#4a90d9):** Tech blue for interactive elements
- **Tertiary (#00ff88):** Neon green for success/active states
- **Warning (#ffaa00):** Amber for warnings
- **Error (#ff4444):** Red for errors
- **On Surface (#ffffff):** Clean white for main content
- **On Surface Variant (#8888aa):** Muted purple-gray for labels

## Typography

- **Segoe UI:** Primary font for all interface elements - clean, modern, and legible
- **Consolas:** Monospace font for values and technical data - ensures consistent alignment
- **Bold weights:** Used for headings and important values
- **Regular weights:** Used for body text and labels
- **Value fonts:** Larger sizes with bold weight for numerical displays

## Layout

- **Panel Width:** 320px for parameter panel
- **Main Content:** Takes remaining space with the steering wheel as centerpiece
- **Status Bar:** 36px fixed height at bottom
- **Wheel Canvas:** Expands to fill available space, maintaining aspect ratio
- **Spacing Scale:** 4px increments for consistent layout

## Elevation & Depth

Layers from back to front:
1. Window background (#0a0a14)
2. Main panels (#16162a)
3. Cards and inputs (#1a1a3e)
4. Active elements (accent colors)
5. Status indicators (glowing effects)

## Shapes

- **Buttons:** 8px rounded corners
- **Panels:** 12px rounded corners
- **Inputs:** 8px rounded corners
- **Sliders:** Full rounded track (pill shape)
- **Status lights:** Circular with glow effect

## Components

### Steering Wheel
- Central focus of the UI
- Real-time rotation animation
- Angle indicators at ±30°, ±60°, ±90°
- Turn direction arrows (left/right) highlighted by accent colors
- Dead zone visual feedback with subtle color change
- Center indicator line

### Parameter Panel
- Collapsible sections with headers
- Sliders with real-time value display
- Preset selector dropdown
- Curve type radio buttons styled as toggles
- Hotkey configuration section
- DPI input with unit conversion

### Status Bar
- Left: Power status indicator (green/red)
- Center: Current steering angle in Consolas font
- Right: Simulation status and mode indicator

### OSD Overlay
- Center-top position
- Dark semi-transparent background
- Large bold text using value-lg typography
- Auto-hide after 2 seconds

### Toggle Buttons
- Inactive: Dark background with muted text
- Active: Secondary (blue) background with white text
- Smooth transition on hover

### Sliders
- Dark track with thin border
- Blue thumb matching secondary accent
- No ticks - clean minimalist design

## Do's and Don'ts

**Do:**
- Use accent colors sparingly for important actions
- Maintain high contrast for text readability
- Keep animations smooth and subtle
- Provide immediate visual feedback
- Use Consolas for all numerical values
- Keep UI elements aligned to 4px grid

**Don't:**
- Overuse multiple accent colors in one area
- Use bright colors for backgrounds
- Make text smaller than 11px
- Use harsh animation effects
- Mix font families within a single element
- Use sharp corners on interactive elements
