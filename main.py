import sys
from database import DatabaseManager
from MainController import MainController
from views import ConsoleView

def main():
    """
    נקודת הכניסה (Entry Point) של אפליקציית הרולטה.
    כאן בעצם התוכנית שלנו מתחילה לרוץ בפועל. אנחנו בונים פה את כל חלקי ה-MVC
    ומחברים אותם יחד לפני שאנחנו מדליקים את הלולאה.
    """
    
    # שלב מס' 1: הפעלת מסד הנתונים SQLite
    # נוצר חיבור לקובץ 'casino.db'. אם הוא לא קיים, הוא נוצר מאחורי הקלעים בעזרת DatabaseManager
    db = DatabaseManager("casino.db")
    
    # שלב מס' 2: הקמת ה- Controller (מנהל הלוגיקה המרכזי)
    # אנחנו מעבירים לו כפרמטר את מסד הנתונים כדי שהוא תמיד יוכל לגשת למידע ולשמור שינויים בחשבון השחקן
    controller = MainController(db)
    
    # שלב מס' 3: הפעלת תצוגת הקונסול (ה-View)
    # התצוגה פה מקבלת אליה את מנהל הלוגיקה, כך שהיא תוכל להעביר פקודות של השחקן מהמקלדת ישירות למוח של התוכנית
    view = ConsoleView(controller)
    
    try:
        # התחלת המשחק ולולאת ה-REPL
        view.start()
    except KeyboardInterrupt:
        # תפיסת מצב שבו המשתמש לוחץ על CTRL+C כדי לסגור את התוכנית בפתאומיות והדפסת הודעה יפה במקום שגיאה
        print("\nForce quitting... Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    # חלק זה מבטיח שהקוד ירוץ רק אם מריצים את הקובץ הזה ספציפית דרך המסוף, ולא כשמייבאים אותו ממקום אחר
    main()
