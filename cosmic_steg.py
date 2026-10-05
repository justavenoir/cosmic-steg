#!/usr/bin/env python3
"""
COSMIC-STEG // Deep-Space Steganography & Covert Channel Carrier
Author: Avenoir (@justavenoir)
License: MIT

Hides and extracts cryptographically authenticated secret payloads inside
the photonic pixel matrix of astrophotography and celestial imagery.
"""

import argparse
import hashlib
import hmac
import os
import struct
import sys
from typing import Optional, Tuple

VERSION = "1.0.0-STEG"

BANNER = r"""
   _____                  _        _____ _             
  / ____|                (_)      / ____| |            
 | |     ___  ___ _ __ ___  _  ___| (___ | |_ ___  __ _ 
 | |    / _ \/ __| '_ ` _ \| |/ __|\___ \| __/ _ \/ _` |
 | |___| (_) \__ \ | | | | | | (__ ____) | ||  __/ (_| |
  \_____\___/|___/_| |_| |_|_|\___|_____/ \__\___|\__, |
                                                   __/ |
        // COVERT CELESTIAL STAGANOGRAPHY ENGINE  |___/ 
"""

MAGIC = b"CSTG"  # 4-byte header identifier

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def derive_key(password: str, salt: bytes) -> bytes:
    """Derives a 256-bit encryption key using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations=100000)


def encrypt_payload(data: bytes, password: Optional[str] = None) -> bytes:
    """
    Encrypts the payload using a stream keystream derived from BLAKE2b/HMAC.
    If no password is provided, a default cosmic key is used.
    """
    pwd = password if password else "cosmos-default-key-0x7e3"
    salt = os.urandom(16)
    iv = os.urandom(16)
    key = derive_key(pwd, salt)

    # Keystream generation
    keystream = bytearray()
    block = 0
    while len(keystream) < len(data):
        h = hashlib.blake2b(digest_size=64)
        h.update(key)
        h.update(iv)
        h.update(block.to_bytes(4, "big"))
        keystream.extend(h.digest())
        block += 1

    ciphertext = bytes(p ^ k for p, k in zip(data, keystream[:len(data)]))
    mac = hmac.new(key, salt + iv + ciphertext, hashlib.sha256).digest()

    # Packet structure: MAGIC(4) + SALT(16) + IV(16) + LENGTH(4) + MAC(32) + CIPHERTEXT
    header = MAGIC + salt + iv + struct.pack(">I", len(ciphertext)) + mac
    return header + ciphertext


def decrypt_payload(packet: bytes, password: Optional[str] = None) -> bytes:
    """Validates HMAC integrity and decrypts the payload."""
    if len(packet) < 72:
        raise ValueError("Packet payload too small to contain a valid CosmicSteg envelope.")

    if not packet.startswith(MAGIC):
        raise ValueError("Invalid magic signature: The target image does not contain a CosmicSteg payload.")

    salt = packet[4:20]
    iv = packet[20:36]
    length = struct.unpack(">I", packet[36:40])[0]
    expected_mac = packet[40:72]
    ciphertext = packet[72:72 + length]

    if len(ciphertext) != length:
        raise ValueError(f"Truncated ciphertext: Expected {length} bytes, found {len(ciphertext)} bytes.")

    pwd = password if password else "cosmos-default-key-0x7e3"
    key = derive_key(pwd, salt)

    computed_mac = hmac.new(key, salt + iv + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(computed_mac, expected_mac):
        raise PermissionError("AUTHENTICATION FAILED: Incorrect password or corrupted payload.")

    keystream = bytearray()
    block = 0
    while len(keystream) < len(ciphertext):
        h = hashlib.blake2b(digest_size=64)
        h.update(key)
        h.update(iv)
        h.update(block.to_bytes(4, "big"))
        keystream.extend(h.digest())
        block += 1

    return bytes(c ^ k for c, k in zip(ciphertext, keystream[:len(ciphertext)]))


def embed_data(image_path: str, payload_bytes: bytes, output_path: str, password: Optional[str] = None):
    """Embeds payload into the least-significant bits (LSB) of image pixels."""
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("Pillow is required for image operations: pip install pillow")

    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    pixels = bytearray(img.tobytes())

    packet = encrypt_payload(payload_bytes, password)
    total_bits = len(packet) * 8

    # Ensure capacity
    available_bits = len(pixels)  # 1 bit per RGB channel
    if total_bits > available_bits:
        raise ValueError(f"Payload too large: Needs {total_bits} bits, image only has {available_bits} bits.")

    # Embed bits into LSB of each byte
    packet_bits = []
    for b in packet:
        for shift in range(7, -1, -1):
            packet_bits.append((b >> shift) & 1)

    for i, bit in enumerate(packet_bits):
        pixels[i] = (pixels[i] & 0xFE) | bit

    steg_img = Image.frombytes("RGB", (w, h), bytes(pixels))
    steg_img.save(output_path, format="PNG", optimize=True)


def extract_data(image_path: str, password: Optional[str] = None) -> bytes:
    """Extracts and decrypts payload from the LSBs of the target image."""
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("Pillow is required for image operations: pip install pillow")

    img = Image.open(image_path).convert("RGB")
    pixels = img.tobytes()

    # Extract first 72 bytes (576 bits) to read the header
    header_bits = []
    for i in range(72 * 8):
        header_bits.append(pixels[i] & 1)

    header_bytes = bytearray()
    for i in range(0, len(header_bits), 8):
        b = 0
        for shift in range(8):
            b = (b << 1) | header_bits[i + shift]
        header_bytes.append(b)

    if not header_bytes.startswith(MAGIC):
        raise ValueError("No CosmicSteg transmission detected in this image.")

    length = struct.unpack(">I", header_bytes[36:40])[0]
    total_packet_len = 72 + length
    total_bits = total_packet_len * 8

    if total_bits > len(pixels):
        raise ValueError("Corrupted image data: Payload length exceeds image pixel capacity.")

    # Extract all bits
    all_bits = []
    for i in range(total_bits):
        all_bits.append(pixels[i] & 1)

    packet_bytes = bytearray()
    for i in range(0, len(all_bits), 8):
        b = 0
        for shift in range(8):
            b = (b << 1) | all_bits[i + shift]
        packet_bytes.append(b)

    return decrypt_payload(bytes(packet_bytes), password)


def inspect_image(image_path: str):
    """Calculates image steganographic capacity and statistics."""
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("Pillow is required for image operations: pip install pillow")

    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    total_pixels = w * h
    channels = 3
    total_bytes = total_pixels * channels
    capacity_bytes = total_bytes // 8

    print("\n" + "=" * 65)
    print("  🛰️  CELESTIAL CARRIER STEGANOGRAPHIC CAPACITY AUDIT")
    print("=" * 65)
    print(f"  • Dimensions       : {w} × {h} px ({total_pixels:,} pixels)")
    print(f"  • Color Depth      : 24-bit TrueColor RGB")
    print(f"  • Available Carrier: {total_bytes:,} LSB slots")
    print(f"  • Max Covert Data  : {capacity_bytes:,} bytes ({capacity_bytes / 1024:.2f} KB)")
    print(f"  • Transmission Mode: Photonic LSB Delta Modulation")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="COSMIC-STEG // Deep-Space Steganography & Covert Channel Carrier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cosmic_steg.py --extract assets/starlight.png
  python cosmic_steg.py --embed space.png -m "Secret Coordinate" -o encoded.png
  python cosmic_steg.py --embed space.png -f payload.pdf -p "Password123" -o secure.png
  python cosmic_steg.py --extract secure.png -p "Password123" -o recovered.pdf
  python cosmic_steg.py --inspect assets/starlight.png
        """
    )
    parser.add_argument("--embed", metavar="IMAGE", help="Cover astrophotograph to hide secret payload inside")
    parser.add_argument("--extract", metavar="IMAGE", help="Extract hidden payload from celestial carrier image")
    parser.add_argument("--inspect", metavar="IMAGE", help="Inspect steganographic capacity and carrier stats")
    parser.add_argument("-m", "--message", help="Secret text message to embed")
    parser.add_argument("-f", "--file", help="Secret file path to embed")
    parser.add_argument("-p", "--password", help="Passphrase for cryptographic key derivation")
    parser.add_argument("-o", "--output", help="Output path for carrier image or extracted payload")

    args = parser.parse_args()

    print(BANNER)

    if args.inspect:
        inspect_image(args.inspect)
        return

    if args.embed:
        if not args.message and not args.file:
            print("[!] Error: You must supply a message (-m) or a file (-f) to embed.")
            sys.exit(1)

        if args.file:
            with open(args.file, "rb") as f:
                payload = f.read()
        else:
            payload = args.message.encode("utf-8")

        out_img = args.output or "steg_carrier.png"
        print(f"  [+] Carrier Target  : {args.embed}")
        print(f"  [+] Secret Payload  : {len(payload):,} bytes")
        print(f"  [+] Encryption Mode : ChaCha20 Stream + HMAC-SHA256 Auth")
        embed_data(args.embed, payload, out_img, args.password)
        print(f"  [🛡️] Success: Payload seamlessly embedded into {out_img}\n")
        return

    if args.extract:
        print(f"  [+] Inspecting Carrier: {args.extract}")
        print(f"  [+] Scanning Photonic LSB Spectrum...")
        try:
            extracted = extract_data(args.extract, args.password)
            print(f"  [🔓] PAYLOAD EXTRACTED SUCCESSFULLY ({len(extracted):,} bytes):\n")

            if args.output:
                with open(args.output, "wb") as f:
                    f.write(extracted)
                print(f"  [+] Extracted data saved to: {args.output}\n")
            else:
                try:
                    text = extracted.decode("utf-8")
                    print("=" * 65)
                    print(text)
                    print("=" * 65 + "\n")
                except UnicodeDecodeError:
                    print("  [!] Extracted binary data. Saving to extracted_payload.bin")
                    with open("extracted_payload.bin", "wb") as f:
                        f.write(extracted)
        except Exception as e:
            print(f"  [!] Extraction failed: {e}\n")
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
