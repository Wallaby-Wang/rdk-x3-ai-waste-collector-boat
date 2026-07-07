# Contributing

This repository is maintained as a competition engineering project. Keep changes small, reproducible and hardware-aware.

## Development

```bash
python -m pip install -e .[dev]
pytest
```

For RDK X3 hardware work, always record:

- RDK OS version
- camera type and device path
- model file name and SHA256
- serial port name
- ESP32-S3 firmware commit

## Code Style

- Keep RDK runtime code hardware-optional where possible so CI can run without a board.
- Do not commit private photos, raw report drafts, credentials or local serial logs.
- Do not claim a model was trained on custom data unless the dataset and training recipe are included.
