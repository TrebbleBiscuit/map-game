# map-game

Concept text based game where you move between rooms in generated maps. Find the portal and go through it to generate and proceed to the next map. Fight enemies along the way. Not much to do yet.

### Requirements

- [Python](https://www.python.org/downloads/) >= 3.10

If you don't have [Poetry](https://python-poetry.org/docs/) >= 1.2 just make sure you install [`textual`](https://github.com/Textualize/textual)

`pip install textual`

or use requirements.txt you know the drill

### Usage

With Poetry: `poetry run python mapgame/mapgame.py`

Or: `python mapgame/mapgame.py`

### What do you do in game

- Walk around by typing a direction `north`/`n`, `east`/`e`, etc.
- Pay attention to on-screen prompts to `open` chests, `heal` in the medbay, etc
- Find and enter the portal (towards the east) to save the game and progress to the next area
- `melee` or `shoot` enemies that roam around for XP
- Level up to increase strength and max HP
- Collect coins to impress and amaze your friends

##### Tips

- If your HP drops to zero, you'll get most of it back - at the cost of some humanity
- Restore humanity by leveling up and killing enemies
- You heal 1 HP every time you enter an unexplored room
- You lose humanity when going through the portal depening on the number of remaining hostile NPCs
- Enemies that get to a chest before you will steal its loot and get stronger
- If you `run` from combat, you lose nothing but your pride
