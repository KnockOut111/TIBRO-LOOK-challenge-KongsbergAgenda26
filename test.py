import sys
import types

# A magic class that dynamically returns itself for any attribute access
# This completely satisfies any hardware constants (like PixelFormat.RGB888)
class MagicMock:
    def __getattr__(self, name):
        return self

# Instantiate our magic mock object
magic_instance = MagicMock()

# Bind this magic instance as our fake 'pykms' and 'kms' modules
fake_kms = types.ModuleType("pykms")
fake_kms.PixelFormat = magic_instance
fake_kms.PixelFormats = magic_instance
sys.modules["pykms"] = fake_kms
sys.modules["kms"] = fake_kms

# Now import picamzero! The display system check will pass perfectly
from picamzero import Camera

print("Initializing your custom script...")
cam = Camera()

print("Snapping photo on Port 0...")
cam.take_photo("HeiKO.jpg")
