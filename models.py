# models.py
# קובץ זה מכיל את מבני הנתונים העיקריים של המשחק (מודלים).
# כאן אנחנו מיישמים את עקרונות תכנות מונחה עצמים (OOP) כמו קימוס (Encapsulation), ירושה (Inheritance) ופולימורפיזם (Polymorphism).

class Player:
    """
    מייצג שחקן קזינו.
    [עיקרון OOP: קימוס (Encapsulation)] - משתנה היתרה של השחקן מוגן ומוסתר מהחוץ, 
    וניתן לגישה או לשינוי רק דרך מתודות מבוקרות.
    """
    def __init__(self, player_id: int, name: str, starting_balance: float):
        self.player_id = player_id
        self.name = name
        # משתנה פרטי מתחיל בשני קווים תחתונים, מונע ממישהו בחוץ לשנות אותו ישירות (כמו self.__balance = 1000000)
        self.__balance = starting_balance  

    def get_balance(self) -> float:
        """מחזיר את היתרה העדכנית של השחקן."""
        return self.__balance

    def update_balance(self, amount: float):
        """
        מעדכן את היתרה של השחקן.
        כמות חיובית לניצחונות, כמות שלילית להפסדים.
        """
        self.__balance += amount

    def can_afford(self, amount: float) -> bool:
        """מוודא שלשחקן יש מספיק כסף בשביל לבצע את ההימור."""
        return self.__balance >= amount

    def __str__(self):
        """פונקציה מיוחדת שמגדירה איך האובייקט יוצג כשנדפיס אותו למסך (print)."""
        return f"Player(ID={self.player_id}, Name={self.name}, Balance=${self.__balance:.2f})"


class BaseBet:
    """
    מחלקת בסיס אבסטרקטית (כללית) לכל ההימורים.
    [עיקרון OOP: ירושה פולימורפיזם] - כל סוגי ההימורים יירשו (Inheritance) מהמחלקה הזו ויממשו מחדש (Override) את בפונקציות שלה בסגנון פולימורפיזם.
    """
    def __init__(self, amount: float):
        self.amount = amount  # סכום ההימור

    def is_winning_bet(self, winning_number: int) -> bool:
        """
        פונקציה פולימורפית שתמיד תוחזרפים מחדש במחלקות היורשות.
        תפקידה לבדוק האם ההימור זכה בהתאם למספר שיצא ברולטה.
        """
        raise NotImplementedError("Subclasses must implement is_winning_bet()")

    def get_payout_multiplier(self) -> int:
        """
        פונקציה פולימורפית לקבלת יחס התשלום (פי כמה השחקן מרוויח).
        """
        raise NotImplementedError("Subclasses must implement get_payout_multiplier()")
        
    def get_description(self) -> str:
        """התיאור הטקסטואלי של ההימור שיישמר במסד הנתונים."""
        return "Generic Bet"


class NumberBet(BaseBet):
    """
    הימור על מספר ספציפי (Straight Up).
    מחלקה זו יורשת (Inheritance) מ- BaseBet.
    """
    def __init__(self, amount: float, target_number: int):
        super().__init__(amount) # קריאה לבנאי של מחלקת האב בשביל לשמור את סכום הכסף (amount)
        self.target_number = target_number

    def is_winning_bet(self, winning_number: int) -> bool:
        # הזכייה מתרחשת רק אם המספר ברולטה זהה לחלוטין למספר שהשחקן בחר
        return self.target_number == winning_number

    def get_payout_multiplier(self) -> int:
        return 36  # תשלום יחסית גבוה, השחקן מרוויח פי 36 מההשקעה שלו

    def get_description(self) -> str:
        return f"Number {self.target_number}"


class ColorBet(BaseBet):
    """
    הימור על צבע (אדום או שחור).
    מחלקה יורשת (Inheritance).
    """
    # קבוצה של כל המספרים האדומים ברולטה אירופאית קלאסית
    REDS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

    def __init__(self, amount: float, color: str):
        super().__init__(amount)
        self.color = color.lower()  # המרת הצבע לאותיות קטנות (למשל 'red' או 'black')

    def is_winning_bet(self, winning_number: int) -> bool:
        if winning_number == 0:
            return False  # 0 הוא צבע ירוק, ולכן לא אדום ולא שחור
            
        is_red = winning_number in self.REDS
        if self.color == "red" and is_red:
            return True
        if self.color == "black" and not is_red:
            return True
            
        return False

    def get_payout_multiplier(self) -> int:
        return 2  # הימור צבע נותן תשלום של 1:1, כלומר פי שניים עשוי להיות מרוויח מהקרן

    def get_description(self) -> str:
        return f"Color {self.color.capitalize()}"


class ParityBet(BaseBet):
    """
    הימור על זוגי או אי-זוגי (Even או Odd).
    ירושה נוספת מאותה המחלקה. פה ניתן לראות שיש לנו ממשק אחיד פולימורפי,
    כך השולט בקוד (MainController) יודע לעבוד עם פונקציית is_winning_bet בלי לדעת איזה הימור נבחר.
    """
    def __init__(self, amount: float, parity: str):
        super().__init__(amount)
        self.parity = parity.lower()  # 'even' או 'odd'

    def is_winning_bet(self, winning_number: int) -> bool:
        if winning_number == 0:
            return False  # גם אי זוגי וגם זוגי מפסידים על 0 ברולטה
            
        is_even = (winning_number % 2 == 0)
        if self.parity == "even" and is_even:
            return True
        if self.parity == "odd" and not is_even:
            return True
            
        return False

    def get_payout_multiplier(self) -> int:
        return 2

    def get_description(self) -> str:
        return f"Parity {self.parity.capitalize()}"

class GameHistoryRecord:
    """
    DTO (Data Transfer Object) המופקד לשמש כנשא המידע של ההיסטוריה, שחוזר ממסד הנתונים.
    """
    def __init__(self, record_id: int, player_id: int, bet_desc: str, amount: float, status: str, outcome_number: int, timestamp: str):
        self.record_id = record_id
        self.player_id = player_id
        self.bet_desc = bet_desc
        self.amount = amount
        self.status = status
        self.outcome_number = outcome_number
        self.timestamp = timestamp
