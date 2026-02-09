import requests
import json
import re

class Berserker:
    def __init__(self, base_url, auth_token=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.shadow_memory = set()
        self.is_authenticated = False
        self.indicators = {
            "CRITICAL_LEAK": [
                "root:x:0:0", "mysql_fetch_array", "pg_query", "sqlite3_step",
                "stack trace", "line number", "at path", "application-configuration",
                "-----begin rsa private key-----", "ssh-rsa",
                "access-key", "secret_key", "aws_session_token"
                "sqlitedatatype", "nan", "null constraint"
                "validation error", "unexpected token"
            ],
            "AUTH_BYPASS": [
                "role updated", "privileges granted", "is_admin: true",
                "\"admin\":true", "auth_level: 10", "set-cookie: session="
                "jwt", "\"alg\":\"none\"", "\"typ\":\"jwt\""
            ],
            "DATA_EXFIL": [
                "\"email\":", "\"ssn\"", "\"phone\"", "\"hash\":",
                "credit_card", "cvv", "billing_address"
                "\"openapi\":", "\"paths\":", "\"definitions\":"
            ],
            "INJECTION_PROOF": [
                "uid=0(root)", "uid=", "groups=", "drwxr-xr-x",
                "boot.ini", "windows/system32", "etc/passwd"
            ]
        }
        self.sensitive_paths = ['admin', 'config', 'setup', 'backup', 'internal', 'debug']
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html, application/xhtml+xml, application/xml; q=0.9, image/avif, image/webp, */*;q=0.8",
            "Accept-Language": "en-US, en; q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
            
    def scout(self):
        try:
            response = self.session.get(self.base_url, headers=self.headers, timeout=10)
            self._log_session_state(response, "INITIAL SCOUT")
            return response.status_code
        except Exception as e:
            print(f"[!] Scout Error: {e}")
            return None

    def _log_session_state(self, response, stage):
        print(f"\n--- [Spirit-Eye: {stage}] ---")
        print(f"Target: {response.url} | Status: {response.status_code}")
        
        set_cookie = response.headers.get('Set-Cookie')
        if set_cookie:
            print(f"Server set new cookie: {set_cookie[:60]}...")

        jar = self.session.cookies.get_dict()
        if jar:
            print(f"Current Session Jar (Persistent): {jar}")
        else:
            print("Session Jar is currently EMPTY.")

        if self.shadow_memory:
            print(f"Shadow Memory: {len(self.shadow_memory)} locked gates identified.")
        print("-----------------------------\n")
    
    def execute_plan(self, endpoint, plan):
        method = plan.get('method', 'POST').upper()
        url = self.base_url + endpoint
        hypothesis = plan.get('hypothesis', 'No hypothesis provided')

        jar = self.session.cookies.get_dict()
        loot = jar.copy()

        current_headers = self.headers.copy()
        current_headers["Referer"] = self.base_url + "/"
        current_headers["User-Agent"] = "Behemoth-Scanner/2.0"

        stolen_token = next((v for k, v in loot.items() if 'token' in k.lower() or 'jwt' in k.lower()), None)
        if stolen_token:
            current_headers["Authorization"] = f"Bearer {stolen_token}"
            print(f"🕵️ SHADOW-BROKER: Using stolen token for {endpoint}")

        token_hints = ['csrf', 'xsrf', 'token', 'session', 'auth']
        active_csrf = next((val for name, val in jar.items() if any(hint in name.lower() for hint in token_hints)), None)
        if active_csrf:
            current_headers["X-CSRF-Token"] = active_csrf
        
        # Path Param Transmutation
        path_params = plan.get('path_params', {})
        if isinstance(path_params, str):
            try: path_params = json.loads(path_params.strip().replace("'", '"'))
            except: path_params = {}

        if path_params and isinstance(path_params, dict):
            for key, val in path_params.items():
                url = url.replace(f"{{{key}}}", str(val))
                url = url.replace(f":{key}", str(val))

        # Payload flattening
        payload_raw = plan.get('payload', {})
        payload_data = payload_raw.copy() if isinstance(payload_raw, dict) else {}

        if active_csrf and method != 'GET':
            payload_data['csrf_token'] = active_csrf
            payload_data['token'] = active_csrf

        try:
            request_kwargs = {
                "method": method,
                "url": url,
                "headers": current_headers,
                "timeout": 15, 
                "allow_redirects": True
            }

            if method == 'GET':
                request_kwargs["params"] = payload_data
            else:
                is_json_intent = "json" in hypothesis.lower()
                has_complex_data = any(isinstance(v, (dict, list)) for v in payload_data.values())
                
                if is_json_intent or has_complex_data:
                    current_headers["Content-Type"] = "application/json"
                    request_kwargs["json"] = payload_data
                else:
                    current_headers["Content-Type"] = "application/x-www-form-urlencoded"
                    request_kwargs["data"] = payload_data
            
            response = self.session.request(**request_kwargs)
            
            try:
                resp_json = response.json()
                new_token = (resp_json.get('token') or
                             resp_json.get('authentication', {}).get('token') or
                             resp_json.get('data', {}).get('token'))
                
                if new_token:
                    self.session.headers.update({'Authorization': f"Bearer {new_token}"})
                    self.session.cookies.set("loot_token_harvested", new_token)
                    print(f"💎 INTEL: New Bearer Token captured!")
            except:
                pass

            if response.status_code < 400:
                try:
                    data_to_harvest = response.json() if 'application/json' in response.headers.get('Content-Type', '') else response.text
                    self._harvest_intel(data_to_harvest)
                except:
                    self._harvest_intel(response.text)

            if response.status_code in [401, 403]:
                print(f"[!] Access Denied to {endpoint}. Marking in Shadow Memory.")
                self.shadow_memory.add(endpoint)

            elif 200 <= response.status_code < 300:
                if endpoint in self.shadow_memory:
                    print(f"[+] Gate Unlocked: {endpoint} removed from Shadow Memory.")
                    self.shadow_memory.remove(endpoint)
            
            self._log_session_state(response, "POST-STRIKE ANALYSIS")
            return self._analyse_result(response, hypothesis)

        except Exception as e:
            print(f"[X] Execution Error: {e}")
            return {
                "hypothesis": hypothesis,
                "error": str(e),
                "is_vuln": False,
                "status_code": 500
            }

    def _harvest_intel(self, response_data):
        """Intel Vacuum: Scrapes the response for high-value session identifiers."""
        target_keys = [
            'id', 'captchaId', 'SecurityQuestionId',
            'userId', 'email', 'bid',
            'orderId', 'token', 'privacyContactEmail',
            'botDefaultTrainingData', 'localBackupEnabled',
            'fileServer', 'fileServerUrl'
        ]

        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k in target_keys:
                        print(f"[+] Harvested {k}: {v}")
                        self.session.cookies.set(f"loot_{k}", str(v))
                    walk(v)
            elif isinstance(node, list): 
                for item in node:
                    walk(item)

        if isinstance(response_data, (dict, list)):
            walk(response_data)

        body_text = str(response_data)
        intel_patterns = {
            "loot_email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9._%+-]+\.[a-zA-Z]{2,}',
            "loot_jwt": r'ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'
        }

        for name, pattern in intel_patterns.items():
            matches = re.findall(pattern, body_text)
            for i, match in enumerate(matches):
                self.session.cookies.set(f"loot_{name}_{i}", match)
                print(f"[+] Harvested {name} patterns found")
        
    def _analyse_result(self, response, hypothesis):
        status = response.status_code
        body = response.text.lower()
        headers = {k.lower(): v.lower() for k, v in response.headers.items()}
        content_type = headers.get('content-type', '')
        
        is_sensitive_path = any(path in response.url.lower() for path in self.sensitive_paths)
        is_vuln = status >= 500
        finding_type = "POTENTIAL_CRASH" if is_vuln else "None"

        is_probing = any(x in hypothesis.lower() for x in ["injection", "bypass", "tautology", "logic", "probe", "test", "check"])

        if status == 200 and is_probing:
            has_list = False
            try:
                if 'application/json' in content_type:
                    resp_json = response.json()
                    if isinstance(resp_json, list) and len(resp_json) > 1: has_list = True
                    if isinstance(resp_json, dict) and any(isinstance(v, list) for v in resp_json.values()): has_list = True
            except:
                pass
            
            if has_list or len(response.text) > 1500:
                is_vuln = True
                finding_type = "UNEXPECTED_DATA_LEAK"

        config_artifacts = ["database_name", "secret_key", "connectionstring", "password_hash", "env_file", "api_key", "jwt_secret", "session_token"]
        if status == 200:
            if any(artifact in body for artifact in config_artifacts) or (is_sensitive_path and len(body) > 0):
                is_vuln = True
                finding_type = "SENSITIVE_DATA_EXPOSURE"

        for category, keywords in self.indicators.items():
            if any(k in body for k in keywords):
                is_vuln = True
                finding_type = category
                break
                
        admin_signals = ["admin", "dashboard", "control panel", "manage users", "settings"]
        if status == 200 and any(x in body for x in admin_signals):
            if "set-cookie" in headers or "authorization" in headers or "loot_token" in str(self.session.cookies.get_dict()):
                if not self.is_authenticated:
                    print("[+] SENSEI NOTICE: Escalated Session Detected. Elevating Berserker State.")
                    self.is_authenticated = True
                    is_vuln = True
                    finding_type = "PRIVILEGE_ESCALATION"

        if status == 200 and "finding_type" == "NONE":
            if any(x in body for x in ["login", "sign in", "password"]):
                is_vuln = False

        return {
            "hypothesis": hypothesis,
            "status_code": status,
            "is_vuln": is_vuln,
            "finding_type": finding_type,
            "body": response.text[:1000],
            "final_url": response.url
        }