import json

class OpenAPIScanner:
    def __init__(self, spec_path):
        self.spec_path = spec_path

    def scan(self):
        with open(self.spec_path, 'r', encoding="utf-8", errors="ignore") as f:
            spec = json.load(f)

        endpoints = []
        base_url = spec.get("servers", [{}])[0].get("url", "")
        paths = spec.get("paths", {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace', 'connect']:
                    continue

                params = details.get("parameters", [])
                request_body = details.get("requestBody", {})

                endpoints.append({
                    "endpoint": path,
                    "method": method.upper(),
                    "params": params,
                    "body_schema": request_body,
                    "description": details.get("description", ""),
                    "base_context": base_url
                })
        return endpoints