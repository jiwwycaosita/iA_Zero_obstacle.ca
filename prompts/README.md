# Prompts

Ce dossier centralise les invites des agents iA. Chaque fichier `.yaml` correspond à un agent spécifique et contient trois variantes de ton ou de détail :

- **precision** : réponse exhaustive, structurée et très contextualisée.
- **performance** : équilibre entre exhaustivité et rapidité, avec quelques demandes de clarification ciblées.
- **efficacite** : réponse concise qui va droit au but en limitant les relances.

## Fichiers disponibles

- `global_system.yaml` : instructions communes pour le système et la coordination des agents.
- `profile.yaml` : collecte et mise à jour du profil utilisateur.
- `formfill.yaml` : assistance au remplissage de formulaires.
- `finance.yaml` : conseils et analyses financières adaptés au contexte canadien.
- `law.yaml` : analyse et cadrage juridiques.
- `complaint.yaml` : rédaction de plaintes ou réclamations structurées.
- `contract.yaml` : rédaction et révision contractuelles.

## Chargement programmatique

Le module `api/agents/load_prompts.py` propose une fonction utilitaire pour charger un agent et un mode :

```python
from api.agents.load_prompts import load_prompt

text = load_prompt(agent="finance", mode="performance")
```

- `agent` correspond au nom du fichier sans l'extension `.yaml`.
- `mode` doit être l'un de `precision`, `performance` ou `efficacite` (insensible à la casse).
- Une exception est levée si le fichier ou le mode n'existent pas.

## Ajout d'un nouvel agent

1. Créer un fichier `<nom>.yaml` dans `prompts/` contenant les trois clés `precision`, `performance` et `efficacite`.
2. Décrire chaque variation avec le ton et le niveau de détail souhaités.
3. Utiliser `load_prompt` pour vérifier le chargement et l'usage de la nouvelle invite.
