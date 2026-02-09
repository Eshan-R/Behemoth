class ModelRouter:
    SCOUT = "gemma-3-12b-it"
    SPECIALIST = "gemini-2.5-flash"
    ARCHMAGE = "gemini-3-flash-preview"
        
    @classmethod
    def get_model(cls, agent_role: str, intensity="normal"):
        if agent_role == "Warlock":
            return cls.SCOUT
        
        if agent_role == "Berserker":
            return cls.SPECIALIST if intensity != "low" else cls.SCOUT
        
        if agent_role in ["Alchemist", "Paladin"]:
            return cls.ARCHMAGE if intensity == "high" else cls.SPECIALIST
        
        return cls.SCOUT