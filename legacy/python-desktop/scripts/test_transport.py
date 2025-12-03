"""CLI helper to test Firebase transport connectivity."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
	parser = argparse.ArgumentParser(description="Send a diagnostic payload to Firebase.")
	parser.add_argument(
		"--text",
		default="Biome connectivity check",
		help="Sample text to send as clipboard payload.",
	)
	args = parser.parse_args()

	repo_root = Path(__file__).resolve().parents[1]
	sys.path.insert(0, str(repo_root))

	from biome_desktop.diagnostics.transport import run_transport_diagnostics

	result = run_transport_diagnostics(sample_text=args.text)
	print(result.details)
	if result.metadata:
		for key, value in result.metadata.items():
			print(f"  {key}: {value}")
	return 0 if result.success else 1


if __name__ == "__main__":
	raise SystemExit(main())
