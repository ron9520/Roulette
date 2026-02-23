# models.py
# Contains all data structures and business objects for the application.

class Player:
    """
    Represents a Casino Player. Demonstrates Encapsulation by protecting the balance attribute
    and providing controlled access methods.
    """
    def __init__(self, player_id: int, name: str, starting_balance: float):
        self.player_id = player_id
        self.name = name
        self.__balance = starting_balance  # Encapsulated attribute

    def get_balance(self) -> float:
        return self.__balance

    def update_balance(self, amount: float):
        """
        Updates the player's balance. Positive amount for wins, negative for losses.
        """
        self.__balance += amount

    def can_afford(self, amount: float) -> bool:
        return self.__balance >= amount

    def __str__(self):
        return f"Player(ID={self.player_id}, Name={self.name}, Balance=${self.__balance:.2f})"


class BaseBet:
    """
    Abstract Base Class for Bets. Demonstrates Inheritance and Polymorphism.
    """
    def __init__(self, amount: float):
        self.amount = amount

    def is_winning_bet(self, winning_number: int) -> bool:
        """
        Polymorphic method to be overridden by subclasses.
        Returns True if the bet wins based on the rolled number.
        """
        raise NotImplementedError("Subclasses must implement is_winning_bet()")

    def get_payout_multiplier(self) -> int:
        """
        Polymorphic method for payout ratio.
        """
        raise NotImplementedError("Subclasses must implement get_payout_multiplier()")
        
    def get_description(self) -> str:
        return "Generic Bet"


class NumberBet(BaseBet):
    """
    A bet on a specific single number (Straight Up).
    """
    def __init__(self, amount: float, target_number: int):
        super().__init__(amount)
        self.target_number = target_number

    def is_winning_bet(self, winning_number: int) -> bool:
        return self.target_number == winning_number

    def get_payout_multiplier(self) -> int:
        return 36  # 35 to 1 payout implies total return is 36x wager

    def get_description(self) -> str:
        return f"Number {self.target_number}"


class ColorBet(BaseBet):
    """
    A bet on Red or Black.
    """
    REDS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

    def __init__(self, amount: float, color: str):
        super().__init__(amount)
        self.color = color.lower()  # 'red' or 'black'

    def is_winning_bet(self, winning_number: int) -> bool:
        if winning_number == 0:
            return False
            
        is_red = winning_number in self.REDS
        if self.color == "red" and is_red:
            return True
        if self.color == "black" and not is_red:
            return True
            
        return False

    def get_payout_multiplier(self) -> int:
        return 2  # 1 to 1 payout

    def get_description(self) -> str:
        return f"Color {self.color.capitalize()}"


class ParityBet(BaseBet):
    """
    A bet on Even or Odd.
    """
    def __init__(self, amount: float, parity: str):
        super().__init__(amount)
        self.parity = parity.lower()  # 'even' or 'odd'

    def is_winning_bet(self, winning_number: int) -> bool:
        if winning_number == 0:
            return False
            
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
    Data Transfer Object representing a single played round.
    """
    def __init__(self, record_id: int, player_id: int, bet_desc: str, amount: float, status: str, outcome_number: int, timestamp: str):
        self.record_id = record_id
        self.player_id = player_id
        self.bet_desc = bet_desc
        self.amount = amount
        self.status = status
        self.outcome_number = outcome_number
        self.timestamp = timestamp
