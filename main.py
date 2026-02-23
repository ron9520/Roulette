import sys
from database import DatabaseManager
from MainController import MainController
from views import ConsoleView

def main():
    """
    Entry point for the Roulette Application.
    Initializes the SQLite database, wires it to the MainController, 
    and launches the REPL Console loop.
    """
    # 1. Initialize DB (SQLite)
    db = DatabaseManager("casino.db")
    
    # 2. Initialize Controller (The Brain)
    controller = MainController(db)
    
    # 3. Initialize View and Start
    # We strictly use the ConsoleView REPL as requested by requirements.
    view = ConsoleView(controller)
    
    try:
        view.start()
    except KeyboardInterrupt:
        print("\nForce quitting... Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
