# LinearMouseSim - UI Optimization Product Requirement Document

## Overview
- **Summary**: Optimize and beautify the UI interface of the LinearMouseSim steering wheel simulator, including expanding maximum steering angle to 720° with snap points, fixing steering wheel flickering, and adding modern UI elements.
- **Purpose**: Improve user experience by providing smoother visual feedback, more flexible steering angle configuration, and a more modern, professional-looking interface.
- **Target Users**: Racing game enthusiasts using LinearMouseSim for mouse-to-steering-wheel conversion.

## Goals
- Increase maximum steering angle from 180° to 720°
- Implement auto-snap feature to common angle values (180°, 360°, 540°, 720°) with visual markers
- Eliminate steering wheel canvas flickering during simulation
- Modernize UI elements with gradient backgrounds, shadows, and smooth animations

## Non-Goals (Out of Scope)
- Changing the underlying steering algorithm
- Adding new features beyond UI optimization
- Modifying keyboard/mouse input handling logic
- Changing the application's core functionality

## Background & Context
The current UI is built with basic tkinter widgets. The steering wheel canvas redraws completely on every angle update using `delete('all')`, which causes noticeable flickering. The maximum angle slider is limited to 180°, which is insufficient for users with high-end steering wheels that support multiple rotations.

## Functional Requirements
- **FR-1**: Maximum steering angle slider range expanded from 30-180° to 30-720°
- **FR-2**: Auto-snap functionality for max angle slider: when user releases slider, value snaps to nearest common angle (180°, 360°, 540°, 720°)
- **FR-3**: Visual markers on the max angle slider indicating common snap points
- **FR-4**: Eliminate steering wheel canvas flickering during rotation animation
- **FR-5**: Modern UI elements including gradient backgrounds, shadow effects, and smooth transitions

## Non-Functional Requirements
- **NFR-1**: UI updates must be smooth with no visible flicker (frame rate > 30 FPS)
- **NFR-2**: Auto-snap behavior should be intuitive and not interfere with fine-grained adjustments
- **NFR-3**: Modern UI elements should maintain performance on low-end systems

## Constraints
- **Technical**: Must use tkinter (existing framework), no external GUI libraries
- **Dependencies**: Maintains compatibility with existing configuration system

## Assumptions
- User understands that 720° represents 2 full rotations of a steering wheel
- Common angle values are multiples of 180° (180, 360, 540, 720)

## Acceptance Criteria

### AC-1: Max Angle Range Expansion
- **Given**: The parameter panel is open
- **When**: User moves the "最大舵角" slider
- **Then**: Slider allows values from 30° to 720°
- **Verification**: `programmatic`

### AC-2: Auto-snap to Common Angles
- **Given**: User is adjusting the max angle slider
- **When**: User releases the slider near a common angle (within 15° tolerance)
- **Then**: Slider value automatically snaps to the nearest common angle (180, 360, 540, 720)
- **Verification**: `programmatic`

### AC-3: Snap Point Visual Markers
- **Given**: The max angle slider is visible
- **When**: User views the slider
- **Then**: Common angle snap points are visually marked on the slider track
- **Verification**: `human-judgment`

### AC-4: Steering Wheel Flicker Elimination
- **Given**: Simulation is running and steering wheel is rotating
- **When**: Steering wheel angle updates continuously
- **Then**: No visible flickering or tearing is observed
- **Verification**: `human-judgment`

### AC-5: Modern UI Elements
- **Given**: Application is running
- **When**: User views the main window
- **Then**: UI features modern elements including gradient backgrounds, subtle shadows, and smooth animations
- **Verification**: `human-judgment`

## Open Questions
- [ ] Should the steering wheel canvas display multiple rotation indicators for angles > 180°?
- [ ] Should other sliders also have snap points or just the max angle slider?
