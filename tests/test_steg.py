import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cosmic_steg import (
    embed_data,
    extract_data,
    encrypt_payload,
    decrypt_payload,
    derive_key,
)

class TestCosmicSteg(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_image = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "assets", "starlight.png")
        )

    def test_pre_embedded_easter_egg(self):
        self.assertTrue(os.path.exists(self.test_image), "Sample starlight carrier should exist")
        extracted = extract_data(self.test_image)
        text = extracted.decode("utf-8")
        self.assertIn("Avenoir (@justavenoir)", text)
        self.assertIn("DEEP-SPACE TRANSMISSION INTERCEPT", text)
        self.assertIn("Learn how it works", text)

    def test_custom_payload_encryption(self):
        secret = b"Cybersecurity zero-day intelligence report // classified 0x7E3"
        pwd = "StarlightSecretKey2026!"
        packet = encrypt_payload(secret, pwd)
        recovered = decrypt_payload(packet, pwd)
        self.assertEqual(secret, recovered)

    def test_wrong_password_fails_authentication(self):
        secret = b"Confidential system telemetry payload"
        packet = encrypt_payload(secret, "CorrectPassword")
        with self.assertRaises(PermissionError):
            decrypt_payload(packet, "WrongPassword")

    def test_roundtrip_embed_extract(self):
        temp_carrier = "test_temp_carrier.png"
        custom_message = b"Testing roundtrip covert steganography channel under simulated conditions."
        try:
            embed_data(self.test_image, custom_message, temp_carrier, password="CustomPassphrase!")
            extracted = extract_data(temp_carrier, password="CustomPassphrase!")
            self.assertEqual(custom_message, extracted)
        finally:
            if os.path.exists(temp_carrier):
                os.remove(temp_carrier)

if __name__ == "__main__":
    unittest.main()
