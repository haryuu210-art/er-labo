# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import research_character
result = research_character.research_character("Coraline", "Coraline")

with open(os.path.join(os.path.dirname(__file__), "test_result.txt"), "w", encoding="utf-8") as f:
    import json
    f.write("SUCCESS\n")
    f.write(json.dumps(result, ensure_ascii=False, indent=2))
    f.write("\n")
