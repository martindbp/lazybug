import os
import sys
import uvicorn

LOCAL_ONLY = os.getenv('LOCAL_ONLY') is not None

port = sys.argv[1] if len(sys.argv) > 1 else '8000'
port = int(port)

ssl_keyfile = None
ssl_certfile = None
is_ssl = port == 443
host = '127.0.0.1' if LOCAL_ONLY or not is_ssl else '0.0.0.0'  # NOTE: need 127... for localhost.ext cert
if is_ssl:
    # Need to link to ssl files
    ssl_keyfile = 'data/local/ssl_keys/privkey.pem'
    ssl_certfile = 'data/local/ssl_keys/fullchain.pem'
    if not os.path.exists(ssl_keyfile) or not os.path.exists(ssl_certfile):
        print(f'No ssl key/certfile found in data/local/ssl_keys/')
        exit(1)

if __name__ == "__main__":
    uvicorn.run(
        "app.app:app",
        host=host,
        port=port,
        log_level="info",
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
    )
