# Block: ARMORIQ
## Status: PENDING BUILD
## Pentest findings will be written here after the block is built.

### Overview
AI security layer using pytector and optional ArmorIQ API for prompt injection detection.

### Components
1. **ArmorIQGuard** - Input/output checking
2. **ArmorIQMiddleware** - FastAPI middleware for request security

### Features
- Prompt injection detection (local + API)
- Input sanitization with bleach
- Output validation
- Attack logging

### Security Requirements
- All user inputs must pass through guard
- Detected attacks logged to attack_logger
- Rate limiting integration
- Graceful degradation if ArmorIQ API unavailable
