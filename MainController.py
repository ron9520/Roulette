import random
import urllib.request
import urllib.error
import json
from models import Player, NumberBet, ColorBet, ParityBet, BaseBet
from database import DatabaseManager

class MainController:
    """
    The orchestrator. Manages the link between View (Console/GUI) and Model/Database.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.current_player = None

    def login_or_register(self, name: str, default_balance=5000.0) -> Player:
        """
        Attempts to load an existing player by name, otherwise creates a new one.
        """
        player_data = self.db.load_player(name)
        if player_data:
            self.current_player = Player(
                player_data["id"], 
                player_data["name"], 
                player_data["balance"]
            )
        else:
            new_id = self.db.create_player(name, default_balance)
            self.current_player = Player(new_id, name, default_balance)
            
        return self.current_player

    def resolve_spin(self, bet: BaseBet) -> dict:
        """
        Rolls the roulette wheel, calculates wins based on the polymorphic bet type,
        updates model balances, and persists changes to SQLite.
        """
        if not self.current_player.can_afford(bet.amount):
            raise ValueError("Insufficient funds for this bet.")
            
        winning_number = random.randint(0, 36)
        is_win = bet.is_winning_bet(winning_number)
        
        # Calculate financials
        if is_win:
            multiplier = bet.get_payout_multiplier()
            payout = bet.amount * multiplier
            profit = payout - bet.amount
            self.current_player.update_balance(profit)
            status = "WIN"
        else:
            payout = 0
            self.current_player.update_balance(-bet.amount)
            status = "LOSS"
            
        # Persist to database
        self.db.update_player_balance(self.current_player.player_id, self.current_player.get_balance())
        self.db.record_bet_history(
            self.current_player.player_id,
            bet.get_description(),
            bet.amount,
            status,
            winning_number
        )
        
        return {
            "winning_number": winning_number,
            "is_win": is_win,
            "payout": payout,
            "new_balance": self.current_player.get_balance()
        }

    def ask_ai_dealer(self, prompt: str) -> str:
        """
        Requirement: Integration with Ollama.
        Makes a local HTTP call to a Dockerized Ollama instance on port 11434.
        """
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3",  # Assuming standard llama3 model is available
            "prompt": f"You are a snarky casino roulette dealer. Answer this question briefly: {prompt}",
            "stream": False
        }
        
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'))
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "The AI is silent...")
                
        except (urllib.error.URLError, TimeoutError):
            return "Dealer AI is offline. Please make sure Ollama is running in Docker (http://localhost:11434)."
