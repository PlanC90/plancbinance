import argparse
import base64
import json
import sys
import time
import uuid
from datetime import timedelta

try:
    import winreg
except Exception:
    winreg = None

try:
    from nacl.signing import SigningKey
except Exception as e:
    print("PyNaCl is required. Install with: pip install pynacl", file=sys.stderr)
    raise


def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode('ascii')


def get_machine_id() -> str:
    if sys.platform.startswith('win') and winreg:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Cryptography") as k:
                v, _ = winreg.QueryValueEx(k, "MachineGuid")
                if v:
                    return str(v)
        except Exception:
            pass
    return f"MAC-{uuid.getnode():012x}"


def main():
    p = argparse.ArgumentParser(description="Ed25519 License Generator (payload.sig)")
    p.add_argument('--priv-hex', help='Ed25519 private key (64 hex bytes). If omitted, a new key is generated (DEMO).')
    p.add_argument('--machine', help='Target machine id (default: current machine id).')
    p.add_argument('--days', type=int, default=30, help='Validity in days (default: 30)')
    p.add_argument('--edition', default='pro')
    p.add_argument('--features', default='auto,ui', help='Comma-separated feature flags')
    args = p.parse_args()

    # Build signing key
    if args.priv_hex:
        try:
            sk_bytes = bytes.fromhex(args.priv_hex)
            signing_key = SigningKey(sk_bytes)
        except Exception as e:
            print(f"Invalid --priv-hex: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        signing_key = SigningKey.generate()

    verify_key = signing_key.verify_key
    public_key_b64 = base64.b64encode(bytes(verify_key)).decode('ascii')

    machine = args.machine or get_machine_id()
    exp = time.time() + float(timedelta(days=args.days).total_seconds())
    features = [x.strip() for x in (args.features or '').split(',') if x.strip()]

    payload = {
        'machine': machine,
        'exp': exp,
        'edition': args.edition,
        'features': features,
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    sig = signing_key.sign(payload_bytes).signature

    token = f"{b64url(payload_bytes)}.{b64url(sig)}"

    print("PUBLIC_KEY_B64=", public_key_b64)
    if not args.priv_hex:
        print("(NOTE) A NEW PRIVATE KEY WAS GENERATED. Save it securely! Use --priv-hex to reuse it.")
        print("PRIVATE_KEY_HEX=", signing_key.encode().hex())
    print("TOKEN=", token)
    print("PAYLOAD=", json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
