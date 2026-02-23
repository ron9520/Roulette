# AI Roulette - High Roller Edition

A modern, graphical user interface (GUI) for an AI-powered Roulette game, built with Python and PyQt6.

## Features
* **Interactive European Roulette Wheel**: A fully animated, visual roulette wheel that correctly places the ball on the winning number.
* **Betting Dashboard**: A complete betting grid for inside numbers (0, 1-36) and outside bets (Red/Black/Even/Odd).
* **Visual Chip Indicators**: Real-time visual tracking of your selected bets with chip icons (`🪙`) highlighting active selections.
* **Player Stats & Bankroll**: Live tracking of your biggest win and biggest loss, alongside your current bankroll.
* **Recent Outcomes & Hot Numbers**: A panel showing the past 10 spin outcomes and detecting the "Hottest" numbers.
* **Registration & Bankruptcy**: A VIP registration window before starting the game. If you run out of funds, the game securely handles bankruptcy and returns you to the lobby to reload.
* **AI Dealer Commentary**: An integrated AI character that reacts dynamically to your wins and losses with humorous commentary.

## Prerequisites
* Python 3
* PyQt6

## Installation and Execution
1. Clone the repository: `git clone https://github.com/ron9520/Roulette.git`
2. Install the requirement(s): `pip install -r requirements.txt`
3. Run the game: `python casino_gui.py`
