import os
import time
from dotenv import load_dotenv
from rich.live import Live
import traceback

from behemoth.utils.scanner import OpenAPIScanner
from behemoth.utils.dashboard import WarRoom
from behemoth.utils.router import ModelRouter
from behemoth.agents.warlock import Warlock
from behemoth.agents.berserker import Berserker
from behemoth.agents.alchemist import Alchemist
from behemoth.agents.paladin import Paladin

class BattleOrchestrator:
    def __init__(self, swagger_path, base_url): 
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("👹 MANA DEPLETED: GEMINI_API_KEY is missing from your .env file!")
        print(f"[*] Mana Source Detected: {self.api_key[:8]}...")

        self.dashboard = WarRoom()

        # Utility & Agents
        self.scanner = OpenAPIScanner(swagger_path)

        self.warlock = Warlock(self.api_key, ModelRouter.get_model("Warlock"))
        self.alchemist = Alchemist(self.api_key, ModelRouter.get_model("Alchemist"))
        self.paladin = Paladin(self.api_key, ModelRouter.get_model("Paladin"))
        self.berserker = Berserker(base_url)
        self.failure_tracker = {}

    def start_war(self, level="medium"):
        endpoints = self.scanner.scan()
        self.dashboard.add_log("System", f"Map Deciphered: {len(endpoints)} targets identified.")

        try:
            with Live(self.dashboard.layout, refresh_per_second=4):
                for target in endpoints:
                    try:
                        result, plan = self._conduct_strike(target, level)

                        # Shadow Back-Tracking
                        if self.berserker.is_authenticated and self.berserker.shadow_memory:
                            self.dashboard.add_log("System", "★ BREACH DETECTED: Initiating Shadow Backtrack ★")

                            locked_gates = list(self.berserker.shadow_memory)
                            for gate_path in locked_gates:
                                gate_target = next((e for e in endpoints if e['endpoint'] == gate_path), None)

                                if gate_target:
                                    self.dashboard.add_log("Warlock", f"Re-striking {gate_path} with stolen keys...")

                                    backtrack_plan = self.warlock.generate_attack(gate_target, level=level, context="authenticated")
                                    backtrack_result = self.berserker.execute_plan(gate_path, backtrack_plan)

                                    if backtrack_result.get('is_vuln'):
                                        self.dashboard.add_log("Paladin", f"Shadow Strike Success: {gate_path} breached!")
                                        self._handle_reporting(gate_target, backtrack_plan, backtrack_result)
                                        self.berserker.shadow_memory.remove(gate_path)

                    except Exception as e:
                        self.dashboard.add_log("System", f"CRITICAL FAULT on {target.get('endpoint')}: {str(e)}")
                        continue
        
        except Exception as global_err:
            self.dashboard.add_log("System", f"👹 BEHEMOTH COLLAPSE: {str(global_err)}")
            print(traceback.format_exc())

    def _conduct_strike(self, target, level):
        start_time = time.time()
        self.dashboard.update_status(target['endpoint'], target['method'])
        self.dashboard.stats["strikes"] += 1

        if not hasattr(self, 'failure_tracker'):
            self.failure_tracker = {}

        result, plan = None, None
        endpoint = target['endpoint']

        # 1. SCOUTING
        self.dashboard.add_log("Warlock", f"Scouting {target['endpoint']} with {self.warlock.model_id}...")

        loot = {k: v for k, v in self.berserker.session.cookies.get_dict().items() if k.startswith('loot_')}
        context = "default"

        if any(x in target['endpoint'].lower() for x in ['login', 'admin', 'user']):
            if loot:
                self.dashboard.add_log("System", "🎯 LOOT DETECTED: Pivoting to Authenticated Exfilttration!")
                context="authenticated"

        plan = self.warlock.generate_attack(target, level=level, context=context, loot=loot)

        if not plan or (isinstance(plan, dict) and "error" in plan):
            error_msg = plan.get("error") if plan else "Unknown Error"
            self.dashboard.add_log("System", f"Warlock's vision failed: {error_msg}")
            return None, None

        if result and result.get('body'):
            try:
                data = json.loads(result['body'])
                self.berserker._harvest_intel(data)
            except:
                self.berserker._harvest_intel(result['body'])

        # 2. BERSERKER STRIKE
        hypothesis = plan.get('hypothesis', 'No hypothesis provided')
        self.dashboard.add_log("Berserker", f"Striking with payload: {hypothesis}")
        result = self.berserker.execute_plan(target['endpoint'], plan)

        # 3. Transmutation & Escalation
        if result and not result['is_vuln']:
            self.failure_tracker[endpoint] = self.failure_tracker.get(endpoint, 0) + 1
            
            is_high_value = any(key in endpoint.lower() for key in ['admin', 'auth', 'config', 'user', 'secret', 'pass'])
            should_desparate = self.failure_tracker[endpoint] >= 3 or (is_high_value and result['status_code'] in [401, 403])

            if should_desparate:
                self.dashboard.add_log("Alchemist", f"⚠️ DESPERATION MODE: High-tier reasoning required for {endpoint}...")

                original_model = self.alchemist.model_id
                self.alchemist.model_id = ModelRouter.get_model("Alchemist", intensity="high")
                
                refined_plan = self.alchemist.refine_attack(
                    target,
                    plan.get('payload'),
                    result.get('body', '')[:2000],
                    loot = loot,
                    is_desperate=True
                )
                
                if refined_plan and "error" not in refined_plan:
                    plan = refined_plan
                    self.dashboard.add_log("System", "🔮 ARCHMAGE plan formulated. Executing Final Gambit...")
                    result = self.berserker.execute_plan(endpoint, plan)

                self.alchemist.model_id = original_model

            elif result['status_code'] in [400, 401, 403]:
                self.dashboard.add_log("Alchemist", "Attack blocked. Refining payload...")
                
                is_desperate = target['endpoint'] in self.berserker.shadow_memory
                
                refined_plan = self.alchemist.refine_attack(target, plan.get('payload'), result.get('body', '')[:1750], loot=loot, is_desperate=is_desperate)
                if refined_plan and "error" not in refined_plan:
                    plan = refined_plan
                    result = self.berserker.execute_plan(endpoint, plan)
                    
                if result.get('is_vuln'):
                    self.paladin.generate_report(target, result)

        # Reporting
        if result and result.get('is_vuln'):
            self.failure_tracker[endpoint] = 0
            self._handle_reporting(target, plan, result)

        if result and result.get('status_code') == 500:
            self.dashboard.add_log("System", "Target unstable (500). Slowing pace...")
            time.sleep(2)
    
        elapsed = time.time() - start_time
        if elapsed < 6.5:
            wait_time = 6.5 - elapsed
            self.dashboard.add_log("System", f"Cooling down for {wait_time:.1f}s to avoid Rate Limit...")
            time.sleep(wait_time)

        return result, plan

    def _handle_reporting(self, target, plan, result):
        self.dashboard.stats["vulns"] += 1

        critical_types = ["SENSITIVE_DATA_EXPOSURE", "PRIVILEGE_ESCALATION", "UNEXPECTED_DATA_LEAK", "SQL_INJECTION_SUCCESS"]
        if result.get('finding_type') in critical_types:
            self.dashboard.stats["criticals"] += 1
            self.dashboard.add_log("System", "🔥 CRITICAL finding detected. Updating Shadow Memory.")
        
        time.sleep(3)
        self.dashboard.add_log("Paladin", f"VULNERABLITY FOUND at {target['endpoint']}!")
        
        loot = {k: v for k, v in self.berserker.session.cookies.get_dict().items() if k.startswith('loot_')}
        
        report = self.paladin.generate_remediation(
            result,
            target['endpoint'],
            plan.get('payload'),
            loot=loot
        )
        
        self._save_report(target['endpoint'], report)

    def _save_report(self, endpoint, report):
        safe_name = endpoint.replace('/', '_').replace(':', '').replace('?', '_') or "root"
        filename = f"workspace/reports/{safe_name}.md"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"[#] Paladin report saved to {filename}")
