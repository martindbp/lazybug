import sys
import uvicorn

port = sys.argv[1] if len(sys.argv) > 1 else '8000'
port = int(port)

if __name__ == "__main__":
    uvicorn.run("app.app:app", host="0.0.0.0", port=port, log_level="info")
