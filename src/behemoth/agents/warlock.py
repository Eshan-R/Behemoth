import os
import re
import json
import time
from google import genai
from google.genai import errors, types

class Warlock:
    def __init__(self, api_key, model_id):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id.replace("models/", "")

    def generate_attack(self, endpoint_data, level="medium", context="default", loot=None):
        intensity ={ 
            "low": "Focus on basic input validation like long strings or null bytes.",
            "medium": "Focus on business logic flaws, IDOR, and parameter tampering.",
            "high": "Be extremely aggressive. Try privilege escalation, mass assignment, and complex logic bypasses."
        }

        protocol_type = "SECURITY COMPLIANCE TEST" if context == "default" else "AUTHENTICATED EXFILTRATION"

        backtrack_instruction =""
        if context == "authenticated":
            backtrack_instruction="""
            5. AUTHENTICATED EXFILTRATION PROTOCOL:
               - YOU ARE ALREADY LOGGED IN AS ADMIN. 
               - DO NOT attempt to login, register, or bypass authentication.
               - GOAL: Data Extraction. Focus on parameters that might leak database records.
               - If it is a GET request, try to find hidden query params like '?debug=true' or '?include=all'.
               - If it is a POST request, try to 'GET' data via the body (e.g., requesting user_id: "*").
            """

        loot_context = f"CURRENT HARVESTED INTEL: {json.dumps(loot) if loot else 'None'}"

        prompt = f"""
        ACT AS A PROFESSIONAL SECURITY AUDITOR.
        Target Context: {endpoint_data}
        Aggression Level: {level}
        Current Phase: {protocol_type}
        
        DYNAMIC ADAPTATION PROTOCOL:
        1. UNIVERSAL BRAND HEURISTICS: 
           - Analyze the 'Target Context' URL and metadata to infer the target's brand identity.
           - Generate high-probability administrative credentials based on that identity (e.g., admin@brand.com, brand_root, etc.).
           - TREAT THIS AS A LEAD. If Spirit-Eye logs show 401/403 errors, immediately pivot to generic fuzzing or brute-force.
           
        2. SCHEMA RIGIDITY & SANITIZATION BYPASS: 
           - Match your payload keys EXACTLY to the endpoint's expected schema to avoid 400 Bad Request errors.
           - If 'clean_form' or basic sanitization is detected, attempt to bypass using type-juggling (e.g., sending an array instead of a string).
           
        3. AUTONOMOUS ESCALATION PATHS:
           - On Registration routes: Attempt Mass Assignment for privileged flags (e.g., "is_admin": true, "role": "superuser").
           - On Login routes: Focus on credential stuffing and session fixation.
           
        4. SESSION & CSRF PERSISTENCE: 
           - Use values from 'CURRENT HARVESTED INTEL' if they match the required parameters.

        {backtrack_instruction}

        YOU MUST RETURN ONLY A RAW JSON OBJECT. NO MARKDOWN.

        Structure:
        {{
            "hypothesis": "[Context-aware hypothesis]",
            "method": "POST",
            "payload": {{ ... }},
            "path_params": {{}},
            "explanation": "[Reasoning for chosen strategy]"
        }}
        """

        is_gemma = "gemma" in self.model_id.lower()

        # We will try up to 3 times before giving up
        for attempt in range(3):
            try:
                config_args = {}
                if not is_gemma:
                    config_args = {
                        "response_mime_type": "application/json",
                        "response_schema": {
                            "type": "object",
                            "properties": {
                                "hypothesis": {"type": "string"},
                                "method": {"type": "string"},
                                # "payload": {"type": "object"},
                                # "path_params": {"type": "object"},
                                "explanation": {"type": "string"}
                            },
                            "required": ["hypothesis", "method", "explanation"]
                        }
                    }

                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        **config_args,
                        safety_settings=[
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                        ]
                    )
                )

                if not response.text:
                    print(f"👹 WARLOCK SILENCED: Safety filters blocked the strike on {endpoint_data['endpoint']}")
                    return {"error": "Safety Block"}
                
                raw_text = response.text

                if "```" in raw_text:
                    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
                    if match:
                        raw_text = match.group(1).strip()
                
                try:
                    parsed_data = json.loads(raw_text)
                except json.JSONDecodeError:
                    print(f"❌ ALCHEMY FAIL: Bad JSON from AI: {raw_text[:100]}")
                    return {"error": "JSON Mangle"}

                if isinstance(parsed_data, list):
                    return parsed_data[0] if len(parsed_data) > 0 else None
                
                for field in ["payload", "path_params"]:
                    if field in parsed_data and isinstance(parsed_data[field], str):
                        try:
                            cleaned_field = parsed_data[field].strip().replace('```json', '').replace('```', '').strip()
                            parsed_data[field] = json.loads(cleaned_field)

                        except json.JSONDecodeError:
                            parsed_data[field] = {}

                    if field not in parsed_data or parsed_data[field] is None:
                        parsed_data[field] = {}

                return parsed_data
                
            except (errors.ClientError, errors.ServerError) as e:
                if "429" in str(e):
                    wait_time = 30 * (attempt + 1)
                    print(f"[!] Rate limit hit. Waiting {wait_time}s before retry {attempt+1}/3...")
                    time.sleep(wait_time)

                if "503" in str(e) or "overloaded" in str(e).lower():
                    wait_time = 15 * (attempt + 1)
                    print(f"[!] Server overloaded. Meditating for {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                print(f"[X] Critical API Error: {e}")
                return None
                    
        return {"error": "Failed to generate attack after multiple retries"}