# Fixtures (TASK-10)

Drop REAL Defender-wrapped report samples here to lock in parser behavior.

Naming: `<expected-rid>__<short-description>.eml`
e.g. `abc1234__outlook-desktop-tnef.eml`, `xy99__owa-rfc822.eml`

Capture samples across the clients you support (Outlook desktop, OWA, new
Outlook) and the "Microsoft + custom mailbox" vs "custom only" reporting
settings — they wrap differently. `test_real_fixtures` asserts each one.

Do NOT commit samples containing real personal data without scrubbing.
