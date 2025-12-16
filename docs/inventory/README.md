# Biome Desktop Inventory

This folder contains a current-state report of the .NET desktop rewrite as of December 2025. Use the individual files below for deep dives:

- `overview.md` – generic host wiring, DI graph, and project boundaries.
- `configuration.md` – source of truth for `BiomeSettings`, appsettings layering, and environment overrides.
- `clipboard.md` – capture service, passive watcher, and clipboard payload formats.
- `dispatch.md` – channel-based queue and the background dispatcher that drives transports.
- `tray.md` – temporary NotifyIcon implementation, command surface, and icon state logic.
- `windowing.md` – console window behavior, navigation shell, settings UI, and dashboard actions.
- `transport.md` – Firebase transport placeholder, OAuth flow, and outbox handling.
- `status.md` – list of idle or legacy remnants discovered during the sweep.

The intention is to keep these documents short, code-backed, and auditable. When functionality changes, update the relevant snippet and call out any new idle paths.
