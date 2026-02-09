# 👹 Behemoth
**Behemoth** is a modular, AI-agent offensive security framework designed for autonomous API exploitation and vulnerability research. By leveraging a multi-model "Spirit Circuit," Behemoth moves beyond static pattern matching to conduct context-aware, deep-reasoning security audits.

---

## 🧠 The Spirit Circuit (Tri-Model Architecture)
Behemoth optimizes its "Cognitive Efficiency" by delegating tasks across a specialized model hierarchy:

* **The Warlock (Gemma 3):** The Scout. Optimized for rapid reconnaissance, mapping attack surfaces, and ingesting large OpenAPI specifications.

* **The Berserker (Gemini 2.5 Flash):** The Tactical Executioner. Wields Spirit-Eye to identify logical endpoint relationships and manages Shadow Memory to harvest and share session intelligence (JWTs, IDs) across the collective.

* **The Alchemist (Gemini 3 Flash):** The Shadow Infiltrator. Focused on complex logical mutations, identity manipulation, and uncovering Broken Object Level Authorization (BOLA).

* **The Paladin (Gemini 3 Flash):** The Scribe. Translates raw attack telemetry into structured, professional remediation reports and actionable technical data.

---

# 🔮 Core Features
### 👁️ Spirit-Eye
A specialized logical parsing engine used by the Berserker to identify relationships between endpoints. It allows the framework to understand the functional "flow" of an API rather than treating endpoints as isolated targets.

### 🌑 Shadow Memory
A persistent state-synchronization layer. When an agent (primarily the Berserker) harvests a credential or token, it is instantly synchronized across all active spirits, enabling mid-strike pivots and authentication bypasses.

### 🛡️ Desperation Mode
An adaptive resiliency protocol. If a target server returns 5xx errors or becomes unstable, agents automatically throttle their strike and prioritize audit trail integrity over aggressive exploitation.

---

# 🚀 Getting Started
### Installation
Behemoth is a native system command, portable across Windows, macOS, and Linux.


```bash
# Clone the repository
git clone https://github.com/your-repo/behemoth.git
cd behemoth

# Install as a native command
pip install .
```
### Usage 
Initialize an autonomous strike:

```bash
behemoth --url <TARGET_URL> --spec <API_SPEC_PATH> --level <low/medium/high>
```
---
## 📊 Evidence of Conquest
In standard audit cycles against environments like **OWASP Juice Shop**, Behemoth has demonstrated:
* **Full Admin Bypass:** Automated SQL Injection on authentication endpoints.

* **Data Exfiltration:** Successful BOLA exploitation leading to mass account harvesting.

* **Audit Integrity:** 100% retention even during server-side overloads (503 errors).

**"Strike hard, strike fast."**