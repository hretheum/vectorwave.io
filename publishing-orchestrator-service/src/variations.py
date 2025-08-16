from typing import List, Dict, Any


def generate_variations(base_content: str, num: int = 3) -> List[Dict[str, Any]]:
    base = base_content.strip()
    variations: List[Dict[str, Any]] = []
    for i in range(num):
        v = {
            "content": base if i == 0 else f"{base}\n\nVariation #{i+1}: alternate angle.",
            "tone": "default" if i == 0 else ("casual" if i % 2 else "formal"),
            "length": len(base),
        }
        variations.append(v)
    return variations
