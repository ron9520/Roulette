import sys
from MainController import MainController
from models import NumberBet, ColorBet, ParityBet

class ConsoleView:
    """
    המחלקה שתספק לנו את התצוגה. בעזרתה אנחנו עומדים בדרישה עבור פרויקטים לאקדמיה להשתמש
    ב- REPL (Read-Evaluate-Print Loop), שהוא בעצם מסך שחור שמקבל פקודות בקונסול ועובר הלאה בצורה מחזורית ללא הפסקה (while True).
    """
    def __init__(self, controller: MainController):
        # הממשק צריך חיבור ישיר לקונטרולר שהרגע יצרנו בכדי שמישהו (Controller) באמת יעבד את מה שהשחקן רשם.
        self.controller = controller

    def start(self):
        """נקודת ההתחלה של הלולאה המרכזית (REPL)."""
        print("="*40)
        print("AI ROULETTE - CONSOLE EDITION")
        print("="*40)
        
        # מתרגמת את מה שהיוזר כתב וקובעת אותו ב-Controller שפועל. 
        name = input("Enter your VIP Name: ").strip() or "PlayerOne"
        player = self.controller.login_or_register(name)
        
        print(f"\nWelcome back, {player.name}. Your bankroll is ${player.get_balance():.2f}")
        
        # לולאת REPL אינסופית שמציגה 5 אופציות כנדרש 
        while True:
            print("\n--- OPTIONS MENU ---")
            print("1. Play a Spin (Place Bet) - הימור ולסובב את הרולטה")
            print("2. View History & Stats - צפייה בעבר המשחקים")
            print("3. Clear My History - מחיקת היסטוריית הימורים")
            print("4. Ask the AI Dealer - דיבור עם דילר חכם דרך אולמה גנרטיבית")
            print("5. Exit Casino - יציאה מסודרת מהרולטה")
            
            choice = input(f"\n[Balance: ${self.controller.current_player.get_balance():.2f}] Select option (1-5): ").strip()
            
            # טיפול בתפר (Evaluate) לבחירת היוזר ב-REPL
            if choice == '1':
                self.handle_betting()
            elif choice == '2':
                self.show_history()
            elif choice == '3':
                self.clear_history()
            elif choice == '4':
                self.ask_dealer()
            elif choice == '5':
                print("Cashing out. See you next time!")
                break # יציאה סופית משברת את תהליך ה- True
            else:
                print("Invalid option. Please choose 1-5.")

    def handle_betting(self):
        """מטפל בלוגיקת תצוגה בלבד, מקבל ממשתמש מספרים וקורה ל-Controller לסובב."""
        print("\n--- PLACE YOUR BET ---")
        print("1. Number Bet (0-36)")
        print("2. Color Bet (Red / Black)")
        print("3. Parity Bet (Even / Odd)")
        
        b_type = input("Select bet category (1-3): ").strip()
        if b_type not in ['1', '2', '3']:
            print("Invalid category.")
            return
            
        try:
            amount = float(input("Enter wager amount ($): "))
            if amount <= 0:
                print("Wager must be positive.")
                return
        except ValueError:
            print("Amount must be a number.")
            return
            
        if not self.controller.current_player.can_afford(amount):
            print("Insufficient funds!")
            return
            
        bet = None # מאתחל הימור כריק
        
        # יצירת סוג ההימור והמרה לאובייקט מתאים למודלים
        if b_type == '1':
            try:
                num = int(input("Enter number (0-36): "))
                if 0 <= num <= 36:
                    bet = NumberBet(amount, num)
                else:
                    print("Number out of bounds.")
                    return
            except ValueError:
                print("Invalid number.")
                return
        elif b_type == '2':
            col = input("Red or Black? ").strip().lower()
            if col in ['red', 'black']:
                bet = ColorBet(amount, col)
            else:
                print("Invalid color.")
                return
        elif b_type == '3':
            par = input("Even or Odd? ").strip().lower()
            if par in ['even', 'odd']:
                bet = ParityBet(amount, par)
            else:
                print("Invalid parity.")
                return
                
        print("\nSpinning the wheel...")
        # כאן View מעביר את האחריות לעשות עבודה ל- Controller האמיתי 
        result = self.controller.resolve_spin(bet)
        print(f"\n>> The ball landed on: {result['winning_number']} <<")
        
        if result['is_win']:
            print(f"WINNER! Payout: ${result['payout']:.2f}")
        else:
            print(f"LOSS. You lost ${bet.amount:.2f}")
            

    def show_history(self):
        # השגת היסטוריה מה- Controller שמשיג מ- DB
        history = self.controller.db.get_player_history(self.controller.current_player.player_id, limit=10)
        print("\n--- RECENT ACTION ---")
        if not history:
            print("No action recorded yet.")
        else:
            for row in history:
                # DB schema: id, player_id, bet_desc, amount, status, outcome_number, timestamp
                print(f"[{row[6]}] Bet: {row[2]} | Wager: ${row[3]:.2f} | Status: {row[4]} | Rolled: #{row[5]}")

    def clear_history(self):
        confirm = input("Are you sure you want to clear your local history? (y/n): ").strip().lower()
        if confirm == 'y':
            self.controller.db.clear_player_history(self.controller.current_player.player_id)
            print("History cleared.")
            
    def ask_dealer(self):
        question = input("\nAsk the dealer AI a question: ").strip()
        if question:
            print("Thinking...")
            # הפניית תקשורת עם המודל של AI
            response = self.controller.ask_ai_dealer(question)
            print(f"\nDealer AI: {response}")
