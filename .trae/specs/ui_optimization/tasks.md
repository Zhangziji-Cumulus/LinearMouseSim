# LinearMouseSim - UI Optimization Implementation Plan

## [x] Task 1: Expand Max Angle Range to 720°
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - Modify the `ParameterSlider` for max_angle in `parameter_panel.py` to support range 30-720
  - Update `steering_algorithm.py` to remove hardcoded 180° limit and allow up to 720°
  - Update the slider resolution and callback logic
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1: Verify slider range is 30-720° in parameter_panel.py
  - `programmatic` TR-1.2: Verify steering_algorithm.py accepts max_angle values up to 720°
  - `programmatic` TR-1.3: Verify slider correctly passes values to configuration system

## [x] Task 2: Implement Auto-snap Feature for Max Angle Slider
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - Add snap points at 180°, 360°, 540°, 720°
  - Implement snap logic on slider release event
  - Add 15° tolerance for snapping
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1: Slider value snaps to 180 when released at 170-190
  - `programmatic` TR-2.2: Slider value snaps to 360 when released at 345-375
  - `programmatic` TR-2.3: Slider value snaps to 540 when released at 525-555
  - `programmatic` TR-2.4: Slider value snaps to 720 when released at 705-720
  - `programmatic` TR-2.5: Slider does not snap when released outside tolerance range

## [x] Task 3: Add Visual Markers for Snap Points
- **Priority**: medium
- **Depends On**: Task 2
- **Description**: 
  - Draw visual indicator lines on the max angle slider track at snap points
  - Use distinct color for snap point markers
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `human-judgement` TR-3.1: Snap points (180, 360, 540, 720) are visibly marked on the slider

## [x] Task 4: Fix Steering Wheel Canvas Flickering
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - Refactor `SteeringWheelCanvas` to use persistent canvas items instead of `delete('all')` + full redraw
  - Create wheel elements once (outer ring, inner ring, center, spokes) and update their positions using `coords()` and `itemconfig()`
  - Use canvas tags to group related elements for efficient updates
  - Implement partial updates for angle-dependent elements only
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `human-judgement` TR-4.1: No visible flicker when steering wheel rotates continuously
  - `programmatic` TR-4.2: Canvas updates maintain smooth animation at >30 FPS

## [x] Task 5: Modernize UI Elements
- **Priority**: medium
- **Depends On**: Task 4
- **Description**: 
  - Add gradient background effects using canvas
  - Implement shadow effects for panels and buttons
  - Add smooth transition animations for status changes
  - Improve color scheme with modern racing-style palette
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `human-judgement` TR-5.1: UI features gradient backgrounds and shadow effects
  - `human-judgement` TR-5.2: Status transitions have smooth visual feedback
  - `human-judgement` TR-5.3: Overall appearance is modern and professional

## [x] Task 6: Update Steering Wheel for >180° Display
- **Priority**: medium
- **Depends On**: Task 1
- **Description**: 
  - Update `SteeringWheelCanvas` to handle angles >180° visually
  - Add rotation count indicator (e.g., "1x", "2x" for multiple rotations)
  - Adjust tick marks and indicators for larger angle ranges
- **Acceptance Criteria Addressed**: AC-1 (indirectly)
- **Test Requirements**:
  - `human-judgement` TR-6.1: Steering wheel correctly displays angles beyond 180°
  - `programmatic` TR-6.2: Wheel canvas handles max_angle values up to 720°
