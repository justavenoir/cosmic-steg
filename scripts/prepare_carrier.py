import os
import sys

# Add root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cosmic_steg import embed_data

msg = """=================================================================
  🌌 DEEP-SPACE TRANSMISSION INTERCEPT // FREQUENCY: 0x7E3
=================================================================
  [+] SENDER IDENTITY : Avenoir (@justavenoir)
  [+] ROLE            : Cybersecurity Engineer & Space Explorer
  [+] SECURITY LEVEL  : LEVEL-5 [ROOT ACCESS GRANTED]
  [+] PROTOCOL        : POISSON-PHOTONIC-STEGANOGRAPHY v1.0
  [+] TARGET OBJECT   : Star OBJ-01 / Sagittarius A* Vector

  [MISSION DIRECTIVE]
  "Learn how it works. Understand how it breaks. Build it better. Secure it."

  [TRANSMISSION LOG]
  Greetings, Explorer.
  If you are reading this decoded payload, you successfully extracted
  the covert data modulated into the photons of the celestial starfield.

  The perimeter is secure. Zero-Trust matrix is active.
  Feel free to inspect my tools or build resilient software together.

  while (alive) { learn(); build(); secure(); }
================================================================="""

HERE = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(HERE, "..", "assets", "starlight_raw.png")
dest = os.path.join(HERE, "..", "assets", "starlight.png")

embed_data(src, msg.encode("utf-8"), dest)
print(f"Successfully embedded secret easter egg into {dest} ({os.path.getsize(dest)} bytes)")
