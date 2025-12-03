using System;

namespace Biome.Desktop.Core.Payloads;

public sealed record ClipboardPayload(
    string Id,
    ClipboardPayloadKind Kind,
    string? TextContent,
    DateTimeOffset CapturedAtUtc,
    string? SourceApplication = null,
    byte[]? ImageBytes = null
);

public enum ClipboardPayloadKind
{
    Unknown,
    Text,
    Image,
    File
}
