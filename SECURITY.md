# Security Policy

This project controls moving motors and electrical loads. Treat every deployment as safety-sensitive.

## Reporting

Open a GitHub issue for non-sensitive bugs. For sensitive reports, contact the maintainers privately before publishing exploit details.

## Safety Rules

- Test motor direction with propellers removed or lifted out of water.
- Keep `POST /api/control/stop` reachable during live demonstrations.
- Use the ESP32-S3 command timeout; do not disable the firmware stop watchdog.
- Do not expose the RDK service directly to the public internet.
