import sqlite3
from datetime import datetime

class DatabaseManager:
    """
    מנהל מסד הנתונים שמטפל בכל האינטראקציות מול מסד הנתונים SQLite3.
    כאשר המחלקה נוצרת, היא פותחת חיבור ובודקת האם הטבלאות הנדרשות קיימות במידה ולא יוצרת אותן.
    """
    def __init__(self, db_file="casino.db"):
        self.db_file = db_file  # קובץ שעליו נשמר נתוני ה SQLite
        self._initialize_db()

    def _get_connection(self):
        """צורת חיבור אל מסד הנתונים, מתודה שעוזרת לנו לפתוח התקשרות (Connection)."""
        return sqlite3.connect(self.db_file)

    def _initialize_db(self):
        """
        פונקציה זו מרכזת את כל פקודות ה- DDl (Data Definition Language).
        עוברת ויוצרת טבלאות של 'שחקן' ושל 'היסטוריית הימורים'.
        """
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
            # ה-Cursor מריץ שאילתות על מסד הנתונים
            cursor = conn.cursor()
            cursor.execute(query_players)
            cursor.execute(query_history)
            # פעולת commit שומרת את השינויים סופית לקובץ
            conn.commit()

    # --- לוגיקה הקשורה לשחקן (Player) ---
    def load_player(self, name: str) -> dict:
        """
        מבצעת טעינה (Read) של נתוני השחקן מקובץ מסד הנתונים של SQLite.
        אם השחקן לא קיים, הפונקציה מחזירה None.
        """
        query = "SELECT id, name, balance FROM players WHERE name = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # מחליפים את הסימן '?' בערך של השם
            cursor.execute(query, (name,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "balance": row[2]}
        return None

    def create_player(self, name: str, starting_balance: float) -> int:
        """
        יוצר שחקן חדש (Create) ומחזיר את מזהה ה-ID הספציפי שלו מתוך מסד הנתונים.
        """
        query = "INSERT INTO players (name, balance) VALUES (?, ?)"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (name, starting_balance))
            conn.commit()
            # השגת המזהה החדש ש- SQLite נתן לשורה כרגע
            return cursor.lastrowid

    def update_player_balance(self, player_id: int, new_balance: float):
        """
        מעדכן (Update) את התקציב של השחקן בתוך המסד, מופעל לאחר סיום ההימור.
        """
        query = "UPDATE players SET balance = ? WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (new_balance, player_id))
            conn.commit()
            
    def delete_player(self, player_id: int):
        """פועלת עבור (Delete), מחיקת כל הנתונים השייכים לשחקן לחלוטין."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # חייבים קודם למחוק את ההיסטוריה ואז שחקן, למניעת בעיות "מפתח זר" (Foreign Key)
            cursor.execute("DELETE FROM history WHERE player_id = ?", (player_id,))
            cursor.execute("DELETE FROM players WHERE id = ?", (player_id,))
            conn.commit()

    # --- לוגיקה הקשורה להיסטורית המשחקים (History) ---
    def record_bet_history(self, player_id: int, bet_desc: str, amount: float, status: str, outcome_number: int):
        """
        שומרת שורה בהיסטוריית הרולטה לאחר הפעלה - הימור, סכום, תוצאה והאם התבצע רווח או לא.
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
        מושכת ממסר הנתונים את ההיסטוריה העדכנית בהדגש על הזמנים (ORDER BY id DESC). 
        מוגבל ל- 20 משחקים כברירת מחדל כדי לא להעמיס.
        """
        query = "SELECT id, player_id, bet_desc, amount, status, outcome_number, timestamp FROM history WHERE player_id = ? ORDER BY id DESC LIMIT ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (player_id, limit))
            # fetchall() מחזירה את כל השורות שנמצאו
            return cursor.fetchall()
            
    def clear_player_history(self, player_id: int):
        """
        מוחקת במיוחד את היסטורית ההימורים של הישן בלבד מבלי למחוק את השחקן והיתרה שלו.
        """
        query = "DELETE FROM history WHERE player_id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (player_id,))
            conn.commit()
