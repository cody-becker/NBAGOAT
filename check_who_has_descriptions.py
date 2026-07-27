import json

with open("player_descriptions.json") as f:
    descriptions = json.load(f)

with open("career_scores.json") as f:
    careers = json.load(f)

id_to_name = {str(c["player_id"]): c["player_name"] for c in careers}

print(f"{len(descriptions)} descriptions saved so far:\n")

for player_id, text in descriptions.items():
    name = id_to_name.get(player_id, f"(unknown id: {player_id})")
    print(f"--- {name} ---")
    print(text)
    print()