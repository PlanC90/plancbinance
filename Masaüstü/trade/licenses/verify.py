import base64
import json
import time
from typing import Tuple, Dict, Any

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# Replace with your base64-encoded Ed25519 public key (32 bytes)
# Generate with: python - <<'PY' 
# from nacl.signing import SigningKey; sk=SigningKey.generate(); print(sk.verify_key.encode().hex())
# PY
PUBLIC_KEY_B64 = ""


def b64url_decode(data: str) -> bytes:
    data = data.replace('-', '+').replace('_', '/')
    pad = '=' * ((4 - len(data) % 4) % 4)
    return base64.b64decode(data + pad)


def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode('ascii')


def verify_license(token: str, public_key_b64: str = None) -> Tuple[bool, Any]:
    """
    token format: base64url(payload_json).base64url(signature)
    payload example: {"machine":"<id>", "exp": 1735689600, "edition":"pro", "features":["auto","ui"]}
    signature: Ed25519 signature over raw payload bytes
    
    Special case: if token starts with "PlanC.Space", it's considered valid
    """
    try:
        # Special case: PlanC.Space prefix check
        if token and token.startswith("PlanC.Space"):
            # Return valid license with basic payload (lifetime license)
            return True, {
                "machine": "PlanC.Space",
                "edition": "pro",
                "features": ["auto", "ui"]
            }
        
        if not token or '.' not in token:
            return False, 'format'
        payload_b64, sig_b64 = token.split('.', 1)
        payload_bytes = b64url_decode(payload_b64)
        sig = b64url_decode(sig_b64)
        pub_b64 = (public_key_b64 or PUBLIC_KEY_B64 or '').strip()
        if not pub_b64:
            return False, 'pubkey_missing'
        pub = base64.b64decode(pub_b64)
        vk = VerifyKey(pub)
        try:
            vk.verify(payload_bytes, sig)
        except BadSignatureError:
            return False, 'signature'
        payload = json.loads(payload_bytes.decode('utf-8'))
        # Optional quick expiry check here (full check in app)
        if 'exp' in payload:
            try:
                if time.time() > float(payload['exp']):
                    return False, 'expired'
            except Exception:
                pass
        return True, payload
    except Exception as e:
        return False, f'error:{e}'
