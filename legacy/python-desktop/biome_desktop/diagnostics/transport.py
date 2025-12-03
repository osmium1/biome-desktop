"""Connectivity diagnostics for Firebase transport."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from ..payloads.classifier import Payload, PayloadKind
from ..transport.firebase_client import FirebaseTransport


@dataclass
class DiagnosticResult:
	success: bool
	details: str
	metadata: Optional[dict[str, str]] = None


def run_transport_diagnostics(sample_text: str = "Biome connectivity check") -> DiagnosticResult:
	"""Send a sample payload through Firebase to verify connectivity."""

	transport = FirebaseTransport()
	if not transport.is_configured:
		return DiagnosticResult(success=False, details="Firebase config missing.")

	payload = Payload(
		kind=PayloadKind.TEXT,
		data=sample_text,
		metadata={"diagnostic": True, "timestamp": time.time()},
	)

	try:
		metadata = transport.send(payload, raise_on_error=True)
		if metadata is None:
			return DiagnosticResult(success=False, details="Transport did not return metadata.")
		return DiagnosticResult(success=True, details="Payload delivered to Firebase.", metadata=metadata)
	except Exception as exc:  # pylint: disable=broad-except
		return DiagnosticResult(success=False, details=f"Error: {exc}")
