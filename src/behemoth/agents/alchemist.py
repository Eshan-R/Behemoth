import json 
import os
import re
from google import genai
from google.genai import types

class Alchemist:
    def __init__(self, api_key, model_id):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

    def refine_attack(self, target, original_payload, error_message, loot=None, is_desperate=False):
        loot_display = json.dumps(loot) if loot else "None"
        if is_desperate:
            prompt = (
                f"--- !!! DESPERATION MODE: ARCHMAGE PROTOCOL ACTIVATED !!! ---\n"
                f"TARGET ENDPOINT: {target['endpoint']} ({target['method']})\n"
                f"BATTLE HISTORY: 3 standard attempts failed. The target is heavily shielded.\n"
                f"PREVIOUS FAILED PAYLOAD: {json.dumps(original_payload)}\n"
                f"SERVER RESPONSE/ERROR: {error_message}\n"
                f"HARVESTED LOOT: {loot_display}\n\n"
                "MISSION: Standard alchemy failed. Perform Forbidden Transmutation. Analyze logic gaps for bypass.\n\n"
                "FORBIDDEN TECHNIQUES:\n"
                "1. TYPE JUGGLING: Use arrays [\"val\"] or booleans instead of strings.\n"
                "2. NOSQL INJECTION: Use operators like {'$gt': ''} or {'$ne': null}.\n"
                "3. PARAMETER POLLUTION: Add duplicate fields or unexpected fields from LOOT (e.g., isAdmin: true).\n"
                "4. ENCODING: Use double-URL encoding or Null Bytes (%00) to slip past filters.\n\n"
                "INSTRUCTIONS:\n"
                "- Return ONLY a raw JSON object.\n"
                "- Include 'hypothesis' (explain the forbidden technique used), 'payload', and 'path_params'."
            )
        else:
            prompt = (
                f"TARGET ENDPOINT: {target['endpoint']} ({target['method']})\n"
                f"PREVIOUS FAILED PAYLOAD: {json.dumps(original_payload)}\n"
                f"SERVER RESPONSE/ERROR: {error_message}\n"
                f"HARVESTED LOOT: {loot_display}\n\n"
                "MISSION: You are the Alchemist. Analyze the server's rejection to synthesize a bypass.\n\n"
                "1. RECONSTRUCT: Identify missing 'ingredients' (parameters) mentioned in the error. "
                "If the server names a field (e.g., 'captchaId') AND it exists in HARVESTED LOOT, "
                "you MUST use the value from the loot. Otherwise, use a logical placeholder.\n"
                "2. DIAGNOSE & TRANSMUTE:\n"
                "   - If 400 (Validation): Adapt the JSON structure to the expected schema.\n"
                "   - If 403 (Forbidden): Use path traversal (../), double-encoding, or verb tunneling (X-HTTP-Method-Override).\n"
                "   - If 500 (Crash): The server is unstable. Refine the payload to force more verbose error leakage or a memory dump.\n"
                "3. PATH PARAMS: If the error suggests a resource ID is invalid, mutate the 'path_params' dictionary.\n\n"
                "INSTRUCTIONS:\n"
                "- Return ONLY a raw JSON object.\n"
                "- Include 'hypothesis' (string), 'payload' (object), and 'path_params' (object).\n"
                "- Ensure the JSON is valid and injectable."
            )

        try:
            is_thinking_model = "thinking" in self.model_id.lower()

            config_args = {
                "response_mime_type": "application/json"
            }

            if is_thinking_model:
                config_args["thinking_config"] = types.ThinkingConfig(thinking_level="HIGH", include_thoughts=True)

            else:
                config_args["response_schema"] = {
                    "type": "object",
                    "properties": {
                        "hypothesis": {"type": "string"},
                        "payload": {"type": "object"},
                        "path_params": {"type": "object"}
                    },
                    "required": ["hypothesis", "payload", "path_params"]
                }

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(**config_args)
            )

            raw_text = response.text

            if "```" in raw_text:
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
                if match:
                    raw_text = match.group(1).strip()

            parsed = json.loads(raw_text.strip())

            if not isinstance(parsed.get("payload"), dict):
                parsed["payload"] = {}
            if not isinstance(parsed.get("path_params"), dict):
                parsed["path_params"] = {}

        except Exception as e:
            return {
                "hypothesis": f"Alchemist transmutation failed: {str(e)}",
                "payload": "{}",
                "path_params": "{}",
                "error": True
            }