import os
import logging
from app.utils.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RulesEngine:
    def __init__(self):
        self.rules_dir = os.path.join(settings.ax_vault_path, "01_Rules")

    def get_system_prompt_extension(self, context: str = "BACKEND") -> str:
        """
        Layer 3: Rules - Loads site-specific rules based on context.
        """
        rule_file = f"{context.upper()}_RULES.md"
        rule_path = os.path.join(self.rules_dir, rule_file)
        
        rules_content = ""
        if os.path.exists(rule_path):
            with open(rule_path, "r", encoding="utf-8") as f:
                rules_content = f.read()
            logger.info(f"RulesEngine: Loaded rules from {rule_file}")
        else:
            logger.info("RulesEngine: No specific rules found for context.")
            
        if not rules_content:
            return ""
            
        return f"\n\n### [JARVIS OPERATION RULES]\n{rules_content}\n"

rules_engine = RulesEngine()
