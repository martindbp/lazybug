import sys
import uvicorn

port = sys.argv[1] if len(sys.argv) > 1 else '8000'
port = int(port)

ssl_keyfile = None
ssl_certfile = None
if port == 443:
    # Need to link to ssl files
    ssl_keyfile = 'privkey.pem'
    ssl_certfile = 'fullchain.pem'

if __name__ == "__main__":
    uvicorn.run(
        "app.app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
    )
