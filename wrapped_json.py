import json as _json

from merkl import WrappedSerializer

# Wrap the json serializer to indent the data, and allow unicode for Chinese characters
json = WrappedSerializer(_json, indent='\t', ensure_ascii=False)
