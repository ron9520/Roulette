import sqlite3
from datetime import datetime

class DatabaseManager:
    """
    Handles all SQLite database interactions.
    Creates necessary tables on initialization if they don't exist.
    """
    def __init__(self, db_file="casino.db"):
        self.db_file = db_file
        self._initialize_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_file)

    def _initialize_db(self):
        query_players = '''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                balance REAL NOT NULL
            )
        '''
        query_history = '''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER,
                bet_desc TEXT,
                amount REAL,
                status TEXT,
                outcome_number INTEGER,
                timestamp TEXT,
                FOREIGN KEY(player_id) REFERENCES players(id)
            )
        '''
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query_players)
            cursor.execute(query_history)
            conn.commit()

    # --- Player Logic ---
    def load_player(self, name: str) -> dict:
        """
        Loads a player by name. If they don't exist, returns None.
        """
        query = "SELECT id, name, balance FROM players WHERE name = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (name,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "balance": row[2]}
        return None

    def create_player(self, name: str, starting_balance: float) -> int:
        """
        Creates a new player and returns their auto-generated ID.
        """
        query = "INSERT INTO players (name, balance) VALUES (?, ?)"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (name, starting_balance))
            conn.commit()
            return cursor.lastrowid

    def update_player_balance(self, player_id: int, new_balance: float):
        """
        Updates the player's balance in the database.
        """
        query = "UPDATE players SET balance = ? WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (new_balance, player_id))
            conn.commit()
            
    def delete_player(self, player_id: int):
        """Deletes a player and their history completely."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history WHERE player_id = ?", (player_id,))
            cursor.execute("DELETE FROM players WHERE id = ?", (player_id,))
            conn.commit()

    # --- History Logic ---
    def record_bet_history(self, player_id: int, bet_desc: str, amount: float, status: str, outcome_number: int):
        """
        Records the outcome of a roulette spin into history.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = '''
            INSERT INTO history (player_id, bet_desc, amount, status, outcome_number, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (player_id, bet_desc, amount, status, outcome_number, timestamp))
            conn.commit()

    def get_player_history(self, player_id: int, limit: int = 20):
        """
        Retrieves the recent history records for a specific player.
        """
        query = "SELECT id, player_id, bet_desc, amount, status, outcome_number, timestamp FROM history WHERE player_id = ? ORDER BY id DESC LIMIT ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (player_id, limit))
            return cursor.fetchall()
            
    def clear_player_history(self, player_id: int):
        """
        Deletes all history records for a specific player.
        """
        query = "DELETE FROM history WHERE player_id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (player_id,))
            conn.commit()
