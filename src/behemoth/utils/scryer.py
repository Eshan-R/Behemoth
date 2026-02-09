import os
import requests
from googlesearch import search
import time

class WarlockScryer:
    def __init__(self, target_domain):
        self.target = target_domain
        self.save_dir = "workspace/specs/"
        os.makedirs(self.save_dir, exist_ok=True)

        self.dorks = [
            f'site:{self.target} filetype:json "openapi"',
            f'site:{self.target} inurl:swagger.json',
            f'site:{self.target} intitle:"Swagger UI" inurl:/v2/api-docs',
        ]

        def scry_and_absorb(self):
            """Return the path to  downloaded Swagger file or None."""
            print(f"[*] Warlock is scrying the mists for {self.target}...")

            for dork in self.dorks:
                try:
                    for url in search(dork, num_results=3):
                        if ".json" in url or ".yaml" in url:
                            return self._download_specs(url)
                    time.sleep(2)
                except Exception as e:
                    print(f"[!] Scrying Failed: {e}")
            return None
        
        def _download_specs(self, url):
            """Downloads the discovered JSON to the local armory"""
            try:
                clear_target = self.target.replace("http://", "").replace("https://", "").replace("/", "_")
                filename = f"{clear_target}_discovered.json"
                path = os.path.join(self.save_dir, filename)

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }

                print(f"[+] Map discovered at: {url}")
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                with open(path, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(response.text)
                
                print(f"[+] Map abosorbed to: {path}")
                return path
            
            except Exception as e:
                print(f"[!] Failed to absorb map: {e}")
                return None