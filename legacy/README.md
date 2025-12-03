# Legacy Assets

This folder keeps artifacts from the pre-refactor tray prototype (fonts, icons, helper scripts).

Current contents:
- `CustomFont.py`: legacy font injector used by the original monolithic script.
- `fonts/`: Joystix TTF bundle referenced by the old Tk layout.
- `images/`: Tray icons from the legacy build.
- `google-analytics.txt`: Obsolete tracking snippet that should stay out of active code.

Keep these files out of the main runtime path so the new modular desktop app stays clean. When we modernize the UI, migrate only what is still relevant and delete the rest.
