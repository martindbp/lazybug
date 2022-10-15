import os
import sys
import uvicorn

port = sys.argv[1] if len(sys.argv) > 1 else '8000'
port = int(port)

ssl_keyfile = None
ssl_certfile = None
if port == 443:
    # Need to link to ssl files
    ssl_keyfile = 'data/local/ssl_keys/privkey.pem'
    ssl_certfile = 'data/local/ssl_keys/fullchain.pem'
    if not os.path.exists(ssl_keyfile) or not os.path.exists(ssl_certfile):
        print(f'No ssl key/certfile found in data/local/ssl_keys/')
        exit(1)

if __name__ == "__main__":
    uvicorn.run(
        "app.app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
    )
