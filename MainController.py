import random
import urllib.request
import urllib.error
import json
from models import Player, NumberBet, ColorBet, ParityBet, BaseBet
from database import DatabaseManager

class MainController:
    """
    מנהל העבודה (The Controller) של אפליקציית הרולטה בארכיטקטורת ה- MVC.
    זה החלק שמקשר בין הממשק כניסה/יציאה (Views) לבין האלמנטים הדאגים למידע והאחסון (Models & Database).
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager # שמירת הרפרנס למנהל מסד הנתונים
        self.current_player = None # בתחילת התוכנית, עדיין לא התחבר שחקן למערכת

    def login_or_register(self, name: str, default_balance=5000.0) -> Player:
        """
        מנסה לטעון שחקן מהמאגר על פי שמו. אם השם קיים, מביא אותו. אם לא, פותח שחקן חדש.
        """
        player_data = self.db.load_player(name)
        if player_data:
            self.current_player = Player(
                player_data["id"], 
                player_data["name"], 
                player_data["balance"]
            )
        else:
            # מתקבל ID חדש ממסד הנתונים שמייצר אחד רציף למשתמש חדש (AUTOINCREMENT)
            new_id = self.db.create_player(name, default_balance)
            self.current_player = Player(new_id, name, default_balance)
            
        return self.current_player

    def resolve_spin(self, bet: BaseBet) -> dict:
        """
        הפונקציה שמנהלת את לוגיקת הסיבוב ברולטה:
        1. בודקת אם יש מספיק תקציב.
        2. מגרילה מספר למסך הזוכה (0-36).
        3. קוראת לפונקציות הפולימורפיות במחלקה של סוג ההימור כדי לבדוק זכייה וסכום תשלום (Payout).
        4. מעדכנת את שמירת הנתונים במודלים וב- Database.
        """
        if not self.current_player.can_afford(bet.amount):
            raise ValueError("Insufficient funds for this bet.") # השלכת שגיאה אם השחקן ניסה להמר על כסף שכלל לא קיים אצלו
            
        winning_number = random.randint(0, 36) # הגרלת הרולטה האמיתית בעזרת Random (בין 0 ל 36 כמו באירופה)
        is_win = bet.is_winning_bet(winning_number)
        
        # חישוב כספים
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
            
        # הרגע שבו אנחנו מבקשים מה-DB לכתוב את כל הנתונים של המשחק פיזית לקובץ השמירה
        self.db.update_player_balance(self.current_player.player_id, self.current_player.get_balance())
        self.db.record_bet_history(
            self.current_player.player_id,
            bet.get_description(),
            bet.amount,
            status,
            winning_number
        )
        
        # החזרת אובייקט עם תשובות המשחק לטובת ה- views שיוכל להדפיס זאת בקונסול
        return {
            "winning_number": winning_number,
            "is_win": is_win,
            "payout": payout,
            "new_balance": self.current_player.get_balance()
        }

    def ask_ai_dealer(self, prompt: str) -> str:
        """
        דרישת השילוב של AI במסוף:
        מבצע התקשרות HTTP פנימית אל המכולה (Docker) של Ollama שמריצה את מודל llama3
        בכתובת 11434. זה מאפשר לקבל תוכן AI מקומית לחלוטין.
        """
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3",  # הדרישה לשימוש במודל סטנדרטי שנמצא ברקע של Ollama
            "prompt": f"You are a snarky casino roulette dealer. Answer this question briefly: {prompt}",
            "stream": False # נרצה שהתשובה תחזור כבלוק 1 ב- JSON
        }
        
        try:
            # מרכיבים את בקשת הרשת (Request) ושולחים כ-JSON דרגן urllib
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'))
            req.add_header('Content-Type', 'application/json')
            
            # ביצוע הקריאה, פועלת עם Timeout של 5 שניות שאם התוכנה יורדת למטה האפליקציה ב- Python לא תתקע ותקרוס
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "The AI is silent...") # אם הייתה הצלחה מוחזר הטקסט של ה-AI
                
        except (urllib.error.URLError, TimeoutError):
            # טיפול במצב שבו הדוקר כבוי או Ollama לא מותקן - לא נקריס את התוכנה למנהל באקדמיה לעולם!
            return "Dealer AI is offline. Please make sure Ollama is running in Docker (http://localhost:11434)."
