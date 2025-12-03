# Biome Desktop

Biome is transitioning from a Python + pystray prototype into a native Windows
experience built with .NET 10, WPF, and Windows App SDK/WinUI 3. The new code
now lives under `src/` while the complete Python implementation has been
archived inside `legacy/python-desktop` for reference when porting features.

High-level goals and the active roadmap continue to live in
`docs/MASTER_PLAN.md` (strategy) and `docs/CURRENT_WORK.md` (scratchpad).

## Documentation
- `docs/MASTER_PLAN.md`  authoritative plan covering UX flows, platform scope,
  .NET 10 + Windows App SDK 1.8.3 direction, and phased milestones.
- `docs/CURRENT_WORK.md`  rolling task list, SDK research notes, and breakout
  work items for the new WPF shell.
- `docs/CONFIGURATION.md`  how the .NET client reads secrets/options and what
  tooling/runtime versions are required.
- `docs/biome-plan.md`  legacy design log, kept for historical context.

## Repo layout (Dec 2025)
``r
src/
  Biome.Desktop.App/   # WPF shell, hosting bootstrapper, appsettings
  Biome.Desktop.Core/  # Shared configuration + upcoming domain services

legacy/python-desktop/
  biome_desktop/       # Full Python tray implementation
  scripts/, main.py, requirements.txt, etc.
``r

## Current status
-  .NET solution scaffolded with WPF shell, DI/host wiring, clipboard watcher, dispatch queue, and tray lifecycle services.
-  Temporary Windows Forms tray icon replicates the legacy flow (Send clipboard/Share image placeholder/Open console/Exit) and keeps the window hidden until summoned.
-  Configuration pipeline mirrors the old env-driven flow using `appsettings.json` + `BIOME__` environment overrides + `BiomeSettings` options.
-  Firebase transport currently spools payload envelopes to `%USERPROFILE%/.biome/outbox/{guid}.json` until credentials and HTTPS integration are ready.
-  Next focus: wire Firebase Storage/Firestore/FCM APIs plus Windows notifications for send success/failure.
-  Legacy Python client remains runnable under `legacy/python-desktop` for side-by-side validation while we rebuild.

## Platform requirements (matches latest Comet research)
| Component | Minimum | Recommended |
| --- | --- | --- |
| .NET SDK | 8.0 | **10.0.100 (LTS)** |
| Visual Studio | 2022 17.1 | 17.14+ (or VS 2026 preview for built-in .NET 10) |
| Windows App SDK | 1.8.x | **1.8.3 (1.8.251106002)** |
| Windows SDK | 2004 / build 19041 | Latest available via VS installer |
| OS | Windows 10 1809+ | Windows 11 23H2+ |

Windows App SDK extensions now ship through the Visual Studio Marketplace  no
separate installer. Install the 1.8.3 runtime on developer machines when running
the app unpackaged.

## Running the new WPF shell (work-in-progress)
1. Install the prerequisites above (dotnet 10 SDK, VS 2022 workload, Windows App
   SDK runtime 1.8.3).
2. `dotnet restore Biome.Desktop.sln`
3. `dotnet build Biome.Desktop.sln`
4. Launch the app from Visual Studio or `dotnet run --project src/Biome.Desktop.App`.

The window currently displays a placeholder surface while background services
and tray integration are implemented. Real transport logic will arrive once the
.NET port reaches feature parity with the legacy Python client.

## Working with the legacy Python client
If you still need the old implementation for validation or smoke testing:

1. `cd legacy/python-desktop`
2. `pip install -r requirements.txt`
3. `python main.py`

All previously documented environment variables (`BIOME_FCM_DEVICE_TOKEN`,
`BIOME_LOG_LEVEL`, etc.) continue to apply there. Use it to compare tray
behavior while we replicate features in the .NET codebase.
