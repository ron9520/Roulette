import sys
import random
import time
import math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QSizePolicy,
    QDialog, QFormLayout, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush

class AIWorker(QThread):
    response_ready = pyqtSignal(str)
    
    def __init__(self, controller, outcome_data):
        super().__init__()
        self.controller = controller
        self.outcome_data = outcome_data

    def run(self):
        try:
            comment = self.controller.generate_dealer_comment(self.outcome_data)
        except Exception as e:
            comment = f"Hmm, the gears in my AI brain are stuck... ({e})"
        self.response_ready.emit(comment)


class RouletteWheelWidget(QWidget):
    """
    Custom QWidget to paint a real, rotating European Roulette Wheel.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.angle = 0.0
        self.winning_number = None # New state for the ball
        # standard european roulette sequence
        self.numbers = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
        self.reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_angle(self, angle):
        self.angle = angle
        self.update()
        
    def set_winning_number(self, number):
        self.winning_number = number
        self.update()

    def get_color(self, num):
        if num == 0:
            return QColor("#2e8b57") # Green
        elif num in self.reds:
            return QColor("#cc0000") # Red
        else:
            return QColor("#222222") # Black

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height) - 20
        rect = QRectF((width - side) / 2, (height - side) / 2, side, side)

        # Draw outer ring
        painter.setBrush(QBrush(QColor("#d4af37"))) # Gold
        painter.drawEllipse(rect.adjusted(-10, -10, 10, 10))

        # Rotate entire wheel
        painter.translate(rect.center())
        painter.rotate(self.angle)
        painter.translate(-rect.center())

        num_slots = len(self.numbers)
        span_angle = 360.0 / num_slots
        
        for i, n in enumerate(self.numbers):
            start_angle = i * span_angle
            start_angle16 = int(start_angle * 16)
            next_angle16 = int((i + 1) * span_angle * 16)
            span_angle16 = next_angle16 - start_angle16
            
            painter.setBrush(QBrush(self.get_color(n)))
            painter.setPen(QPen(QColor("#d4af37"), 2))
            
            painter.drawPie(rect, start_angle16, span_angle16)

            # Draw Number Text
            painter.save()
            painter.translate(rect.center())
            painter.rotate(-start_angle - (span_angle / 2))
            painter.setPen(QPen(Qt.GlobalColor.white))
            font = QFont("Arial", max(8, int(side / 30)), QFont.Weight.Bold)
            painter.setFont(font)
            
            # Draw on the positive X-axis (right side) instead of negative X-axis
            text_rect = QRectF(side/2 - 40, -15, 35, 30)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(n))
            painter.restore()

        # Draw the Roulette Ball if there is a winning number
        if self.winning_number is not None:
            try:
                idx = self.numbers.index(self.winning_number)
                ball_angle = idx * span_angle + (span_angle / 2)
                painter.save()
                painter.translate(rect.center())
                painter.rotate(-ball_angle)
                
                # Draw the ball near the inner edge of the numbers slice
                ball_radius = 8
                ball_distance_from_center = side/2 - 65
                
                painter.setBrush(QBrush(QColor("#ffffff"))) # White ball
                painter.setPen(QPen(QColor("#dddddd"), 1))
                painter.drawEllipse(QRectF(ball_distance_from_center - ball_radius, -ball_radius, ball_radius * 2, ball_radius * 2))
                
                painter.restore()
            except ValueError:
                pass # Winning number not in list, ignore

        # Draw center hub
        painter.resetTransform()
        hub_rect = QRectF((width - 60)/2, (height - 60)/2, 60, 60)
        painter.setBrush(QBrush(QColor("#1a1a1a")))
        painter.setPen(QPen(QColor("#d4af37"), 4))
        painter.drawEllipse(hub_rect)
        painter.end()


class CasinoGUI(QMainWindow):
    def __init__(self, main_controller, db_manager):
        super().__init__()
        self.controller = main_controller
        self.db = db_manager

        self.setWindowTitle("AI Roulette - High Roller Edition")
        self.resize(1200, 850)
        self.setStyleSheet("""
            QMainWindow { background-color: #0b0c10; }
            QLabel { color: #c5c6c7; }
            QPushButton { 
                background-color: #1f2833; color: #66fcf1; 
                border-radius: 5px; font-weight: bold; padding: 10px; border: 2px solid #45a29e;
            }
            QPushButton:hover { background-color: #45a29e; color: #0b0c10; }
            QPushButton:pressed { background-color: #66fcf1; color: #000; }
            QLineEdit { 
                background-color: #1f2833; color: #66fcf1; 
                border: 2px solid #45a29e; border-radius: 5px; padding: 8px; font-size: 16px; font-weight: bold;
            }
        """)

        # Game State
        self.selected_bet_type = None
        self.selected_pick = None
        self.player_name = self.controller.get_player_name()
        self.balance = self.controller.get_player_balance()
        self.biggest_win = 0.0
        self.biggest_loss = 0.0
        self.is_bankrupt = False
        
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self._type_next_char)
        self.full_ai_message = ""
        self.current_typed_message = ""
        self.typing_index = 0

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # 1. Top Dashboard Strip
        top_bar = QHBoxLayout()
        self.name_label = QLabel(f"VIP 👤: {self.player_name}")
        self.name_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #d4af37;") # Casino Gold
        
        self.balance_label = QLabel(f"Bankroll: ${self.balance:,.2f}")
        self.balance_label.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
        self.balance_label.setStyleSheet("color: #66fcf1; background: #1f2833; padding: 5px 15px; border-radius: 5px;")
        
        top_bar.addWidget(self.name_label)
        top_bar.addStretch()
        top_bar.addWidget(self.balance_label)
        main_layout.addLayout(top_bar)

        # 2. Main Game Area (Wheel + Betting)
        game_layout = QHBoxLayout()
        
        # Wheel Section (Left)
        wheel_container = QVBoxLayout()
        self.wheel_widget = RouletteWheelWidget()
        wheel_container.addWidget(self.wheel_widget, 2)
        
        self.outcome_label = QLabel("PLACE YOUR BETS")
        self.outcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.outcome_label.setFont(QFont("Segoe UI", 24, QFont.Weight.ExtraBold))
        self.outcome_label.setStyleSheet("color: #d4af37; letter-spacing: 2px;")
        wheel_container.addWidget(self.outcome_label)

        # Recent Outcomes Panel
        recent_panel = QHBoxLayout()
        self.recent_outcomes = []
        
        recent_label = QLabel("Recent: ")
        recent_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.recent_display = QLabel("None")
        self.recent_display.setFont(QFont("Segoe UI", 14, QFont.Weight.Normal))
        self.recent_display.setStyleSheet("color: #c5c6c7; background: #1f2833; padding: 5px; border-radius: 3px;")
        
        hot_label = QLabel(" | Hot: ")
        hot_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.hot_display = QLabel("None")
        self.hot_display.setFont(QFont("Segoe UI", 14, QFont.Weight.Normal))
        self.hot_display.setStyleSheet("color: #cc0000; font-weight: bold;")
        
        recent_panel.addWidget(recent_label)
        recent_panel.addWidget(self.recent_display, 1)
        recent_panel.addWidget(hot_label)
        recent_panel.addWidget(self.hot_display)
        wheel_container.addLayout(recent_panel)

        game_layout.addLayout(wheel_container, 1)

        # Betting Section (Right)
        betting_container = QVBoxLayout()
        
        # Stats Layout
        stats_layout = QHBoxLayout()
        self.big_win_label = QLabel("🏆 Biggest Win: $0.00")
        self.big_win_label.setStyleSheet("color: #2e8b57; font-weight: bold; font-size: 14px;")
        self.big_loss_label = QLabel("📉 Biggest Loss: $0.00")
        self.big_loss_label.setStyleSheet("color: #cc0000; font-weight: bold; font-size: 14px;")
        stats_layout.addWidget(self.big_win_label)
        stats_layout.addWidget(self.big_loss_label)
        betting_container.addWidget(QLabel("Player Stats:"))
        betting_container.addLayout(stats_layout)

        # Selected Bet Area
        self.bet_info_label = QLabel("🎯 Selected Bet: None")
        self.bet_info_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        betting_container.addWidget(self.bet_info_label)

        # Number Grid Layout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)
        self.bet_buttons = {} # Store buttons to update icons later
        
        zero_btn = QPushButton("0")
        zero_btn.setStyleSheet("background-color: #2e8b57; color: white; border: none; font-size: 18px; padding: 10px;")
        zero_btn.clicked.connect(lambda _, n="0": self.select_bet("Number", n))
        grid_layout.addWidget(zero_btn, 0, 0, 1, 3)
        self.bet_buttons["0"] = zero_btn

        row, col = 1, 0
        reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        for i in range(1, 37):
            btn = QPushButton(str(i))
            color = "#cc0000" if i in reds else "#222222"
            btn.setStyleSheet(f"background-color: {color}; color: white; border: none; font-size: 16px; padding: 10px;")
            btn.clicked.connect(lambda _, n=str(i): self.select_bet("Number", n))
            grid_layout.addWidget(btn, row, col)
            self.bet_buttons[str(i)] = btn
            col += 1
            if col > 2:
                col = 0
                row += 1

        betting_container.addLayout(grid_layout)

        # Outside Bets
        self.outside_buttons = {}
        outside_layout = QHBoxLayout()
        
        btn_red = QPushButton("RED")
        btn_red.setStyleSheet("background-color: #cc0000; color: white; border: none; font-weight: bold; padding: 10px;")
        btn_red.clicked.connect(lambda: self.select_bet("Color", "Red"))
        self.outside_buttons[("Color", "Red")] = btn_red
        
        btn_black = QPushButton("BLACK")
        btn_black.setStyleSheet("background-color: #222222; color: white; border: none; font-weight: bold; padding: 10px;")
        btn_black.clicked.connect(lambda: self.select_bet("Color", "Black"))
        self.outside_buttons[("Color", "Black")] = btn_black

        btn_even = QPushButton("EVEN")
        btn_even.setStyleSheet("background-color: #1f2833; color: white; border: 1px solid #45a29e; font-weight: bold; padding: 10px;")
        btn_even.clicked.connect(lambda: self.select_bet("Parity", "Even"))
        self.outside_buttons[("Parity", "Even")] = btn_even
        
        btn_odd = QPushButton("ODD")
        btn_odd.setStyleSheet("background-color: #1f2833; color: white; border: 1px solid #45a29e; font-weight: bold; padding: 10px;")
        btn_odd.clicked.connect(lambda: self.select_bet("Parity", "Odd"))
        self.outside_buttons[("Parity", "Odd")] = btn_odd

        outside_layout.addWidget(btn_red)
        outside_layout.addWidget(btn_black)
        outside_layout.addWidget(btn_even)
        outside_layout.addWidget(btn_odd)
        betting_container.addLayout(outside_layout)

        # Controls (Amount & Spin)
        controls_layout = QHBoxLayout()
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Bet Amount ($)")
        controls_layout.addWidget(self.amount_input)

        self.spin_btn = QPushButton("🎰 SPIN")
        self.spin_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.spin_btn.setStyleSheet("background-color: #d4af37; color: #000; border: none; padding: 15px;")
        self.spin_btn.clicked.connect(self.start_spin)
        controls_layout.addWidget(self.spin_btn, 1)

        betting_container.addLayout(controls_layout)
        game_layout.addLayout(betting_container, 1)
        
        main_layout.addLayout(game_layout, 2)

        # 3. AI Dealer Bubble
        self.ai_bubble = QLabel("🤖 Dealer AI: Step right up. The tables are hot.")
        self.ai_bubble.setWordWrap(True)
        self.ai_bubble.setFont(QFont("Georgia", 14, QFont.Weight.Normal, True))
        self.ai_bubble.setStyleSheet("""
            background-color: #1f2833; border-left: 5px solid #66fcf1; 
            padding: 15px; border-radius: 5px; color: #c5c6c7; font-size: 18px;
        """)
        main_layout.addWidget(self.ai_bubble)

        # 4. Interactive History Table
        history_label = QLabel("Recent Action")
        history_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        history_label.setStyleSheet("color: #45a29e;")
        main_layout.addWidget(history_label)

        self.history_table = QTableWidget(0, 7)
        self.history_table.setHorizontalHeaderLabels(["ID", "Type", "Pick", "Wager", "Status", "Outcome", "Time"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setStyleSheet("""
            QTableWidget { background-color: #0b0c10; color: #c5c6c7; border: 1px solid #1f2833; }
            QHeaderView::section { background-color: #1f2833; color: #d4af37; font-weight: bold; border: none; }
            QTableWidget::item { padding: 5px; }
        """)
        self.history_table.setFixedHeight(150)
        main_layout.addWidget(self.history_table)

        self.load_history()

    def select_bet(self, bet_type, pick):
        self.selected_bet_type = bet_type
        self.selected_pick = pick
        self.bet_info_label.setText(f"🎯 Selected: {bet_type} | {pick}")
        self.update_chip_visuals()

    def update_chip_visuals(self):
        # Reset all NUMBER button texts and styles
        for n, btn in self.bet_buttons.items():
            color = "#222222" # default black
            if n == "0": color = "#2e8b57" # green
            elif int(n) in {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}:
                color = "#cc0000" # red
            
            # If this is the selected number, add a chip emoji and highlight border
            if self.selected_bet_type == "Number" and n == self.selected_pick:
                btn.setText(f"🪙 {n}")
                btn.setStyleSheet(f"background-color: {color}; color: white; border: 3px solid #d4af37; font-size: 16px; padding: 7px; font-weight: bold;")
            else:
                btn.setText(n)
                btn.setStyleSheet(f"background-color: {color}; color: white; border: none; font-size: 16px; padding: 10px;")
                
        # Reset all OUTSIDE button texts and styles
        for (b_type, pick), btn in self.outside_buttons.items():
            # Determine base color based on pick
            if pick == "Red": color = "#cc0000"
            elif pick == "Black": color = "#222222"
            else: color = "#1f2833" # Even/Odd background
            
            base_style = f"background-color: {color}; color: white; font-weight: bold; padding: 10px;"
            if pick in ("Even", "Odd"):
                base_style += " border: 1px solid #45a29e;"
            else:
                base_style += " border: none;"
                
            if self.selected_bet_type == b_type and self.selected_pick == pick:
                btn.setText(f"🪙 {pick.upper()}")
                # Override border but keep the color for selected outside bets
                btn.setStyleSheet(f"background-color: {color}; color: white; border: 3px solid #d4af37; font-weight: bold; padding: 7px;")
            else:
                btn.setText(pick.upper())
                btn.setStyleSheet(base_style)

    def start_spin(self):
        if not self.selected_bet_type or not self.amount_input.text():
            QMessageBox.warning(self, "Hold On!", "Please select a bet grid and enter an amount.")
            return

        try:
            amount = float(self.amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Wager", "Bet amount must be a number.")
            return

        if amount > self.balance:
            QMessageBox.warning(self, "Insufficient Funds", "You do not have enough bankroll for that bet!")
            return

        if amount <= 0:
            QMessageBox.warning(self, "Invalid Wager", "Bet amount must be greater than zero.")
            return

        # Disable Controls
        self.spin_btn.setEnabled(False)
        self.outcome_label.setText("NO MORE BETS...")
        self.outcome_label.setStyleSheet("color: #66fcf1;")
        
        # Calculate winning result now but reveal it at the end of the animation
        self.pending_outcome_data = self.controller.play_round(amount, self.selected_bet_type, self.selected_pick)
        target_number = self.pending_outcome_data["winning_number"]
        
        self.wheel_widget.set_winning_number(None) # Clear previous ball
        
        # Calculate target angle so the winning number ends up on top
        idx = self.wheel_widget.numbers.index(target_number)
        target_angle = -(idx * (360.0 / 37.0)) 
        
        # Add random extra full rotations (e.g. 5 to 10 spins)
        self.spin_duration = 3000 # 3 seconds
        self.start_angle = self.wheel_widget.angle
        total_rotation = target_angle - self.start_angle - (360 * random.randint(5, 10))
        self.target_exact_angle = self.start_angle + total_rotation

        self.spin_start_time = time.time()
        self.spin_timer = QTimer()
        self.spin_timer.timeout.connect(self._animate_spin)
        self.spin_timer.start(16) # ~60fps
        
        self.set_dealer_message("Spinning the wheel... let's see what the future holds!")

    def _animate_spin(self):
        elapsed = (time.time() - self.spin_start_time) * 1000
        if elapsed >= self.spin_duration:
            self.spin_timer.stop()
            # Lock precisely to the modulo angle so we don't hold huge floats
            final_angle = self.target_exact_angle % 360
            self.wheel_widget.set_angle(final_angle)
            self.resolve_spin()
            return
        
        # Ease-out cubic formula for rotation
        t = elapsed / self.spin_duration
        t -= 1
        eased_progress = (t**3 + 1)
        
        current_angle = self.start_angle + (self.target_exact_angle - self.start_angle) * eased_progress
        self.wheel_widget.set_angle(current_angle)

    def resolve_spin(self):
        outcome = self.pending_outcome_data
        winning_number = outcome["winning_number"]
        self.wheel_widget.set_winning_number(winning_number)
        is_win = outcome["is_win"]
        self.balance = outcome["new_balance"]
        payout = outcome["payout"]

        # Formulate wheel color label
        reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        if winning_number == 0:
            result_color = "#2e8b57"
        elif winning_number in reds:
            result_color = "#cc0000"
        else:
            result_color = "#222222"

        amount_wagered = outcome.get("amount_wagered", 0)
        self.update_recent_outcomes(winning_number)
        
        if is_win:
            profit = payout - amount_wagered
            if profit > self.biggest_win:
                self.biggest_win = profit
                self.big_win_label.setText(f"🏆 Biggest Win: ${self.biggest_win:,.2f}")
            self.outcome_label.setText(f"WINNER: {winning_number}! (+${payout})")
            self.outcome_label.setStyleSheet("color: #66fcf1; font-size: 28px;")
        else:
            if amount_wagered > self.biggest_loss:
                self.biggest_loss = amount_wagered
                self.big_loss_label.setText(f"📉 Biggest Loss: ${self.biggest_loss:,.2f}")
            self.outcome_label.setText(f"OUTCOME: {winning_number}")
            self.outcome_label.setStyleSheet(f"color: {result_color}; font-size: 28px;")

        self.balance_label.setText(f"Bankroll: ${self.balance:,.2f}")
        self.load_history()

        if self.balance <= 0:
            self.trigger_bankrupt_logic()
        else:
            self.ai_bubble.setText("🤖 Dealer AI: Processing the vibe...")
            self.ai_worker = AIWorker(self.controller, outcome)
            self.ai_worker.response_ready.connect(self.set_dealer_message)
            self.ai_worker.start()
            self.spin_btn.setEnabled(True)

    def trigger_bankrupt_logic(self):
        QMessageBox.warning(self, "Bankrupt!", "You ran out of funds!\nReturning to the registration window.")
        self.is_bankrupt = True
        self.close()
        
    def update_recent_outcomes(self, number):
        self.recent_outcomes.insert(0, number)
        if len(self.recent_outcomes) > 10:
            self.recent_outcomes.pop()
            
        recent_str = " - ".join(str(n) for n in self.recent_outcomes)
        self.recent_display.setText(recent_str)
        
        # Calculate Hot Numbers (most frequent in history)
        if len(self.recent_outcomes) >= 5:
            from collections import Counter
            counts = Counter(self.recent_outcomes)
            # Get the top 2 hot numbers
            hot_nums = [str(num) for num, freq in counts.most_common(2) if freq > 1]
            if hot_nums:
                self.hot_display.setText(", ".join(hot_nums))
            else:
                self.hot_display.setText("None yet")
        else:
            self.hot_display.setText("None yet")

    def load_history(self):
        history = self.db.get_history()
        self.history_table.setRowCount(0)
        
        for row_idx, record in enumerate(history):
            self.history_table.insertRow(row_idx)
            for col_idx, item in enumerate(record):
                cell = QTableWidgetItem(str(item))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Colorize win/loss
                if col_idx == 4: # Status
                    if item == "WIN": cell.setForeground(QColor("#66fcf1"))
                    if item == "LOSS": cell.setForeground(QColor("#cc0000"))
                self.history_table.setItem(row_idx, col_idx, cell)

    def set_dealer_message(self, message):
        self.full_ai_message = "🤖 Dealer AI: " + message
        self.current_typed_message = ""
        self.typing_index = 0
        self.typing_timer.start(25) 

    def _type_next_char(self):
        if self.typing_index < len(self.full_ai_message):
            self.current_typed_message += self.full_ai_message[self.typing_index]
            self.ai_bubble.setText(self.current_typed_message)
            self.typing_index += 1
        else:
            self.typing_timer.stop()


# ================================================
# ADVANCED MOCK CLASSES
# ================================================
class MockDatabaseManager:
    def __init__(self):
        self.records = []
        self.counter = 1
        
    def add_record(self, bet_type, pick, amount, status, outcome):
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        record = (self.counter, bet_type, pick, f"${amount:,.2f}", status, outcome, time_str)
        self.records.insert(0, record)
        self.counter += 1

    def get_history(self):
        return self.records

class MockMainController:
    def __init__(self, db_manager, player_name="HighRollerHQ", balance=5000.0):
        self.db = db_manager
        self.balance = balance
        self.player_name = player_name
        self.reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

    def get_player_name(self):
        return self.player_name
        
    def get_player_balance(self):
        return self.balance
        
    def play_round(self, amount, bet_type, pick):
        winning_number = random.randint(0, 36)
        
        is_win = False
        payout_multiplier = 0
        
        if bet_type == "Number":
            if int(pick) == winning_number:
                is_win = True
                payout_multiplier = 36 # 35 to 1 payout, so you get orig amount + 35 = 36x
        elif bet_type == "Color":
            is_red = winning_number in self.reds
            is_black = winning_number != 0 and not is_red
            if (pick == "Red" and is_red) or (pick == "Black" and is_black):
                is_win = True
                payout_multiplier = 2 # 1 to 1 payout
        elif bet_type == "Parity":
            if winning_number != 0:
                is_even = (winning_number % 2 == 0)
                is_odd = not is_even
                if (pick == "Even" and is_even) or (pick == "Odd" and is_odd):
                    is_win = True
                    payout_multiplier = 2
        
        payout = amount * payout_multiplier if is_win else 0
        
        if is_win:
            # Profit formulation: you get back your amount + winnings
            profit = payout - amount
            self.balance += profit
            status = "WIN"
        else:
            self.balance -= amount
            status = "LOSS"
            
        self.db.add_record(bet_type, pick, amount, status, f"#{winning_number}")
        
        return {
            "winning_number": winning_number,
            "is_win": is_win,
            "new_balance": self.balance,
            "payout": payout,
            "amount_wagered": amount
        }

    def reload_balance(self, amount):
        self.balance += amount

    def generate_dealer_comment(self, outcome_data):
        # Simulate local LLM wait
        time.sleep(1.0)
        is_win = outcome_data["is_win"]
        w = outcome_data["winning_number"]
        
        if is_win:
            return random.choice([
                f"Number {w}... Beginner's luck. Enjoy it while it lasts.",
                f"A win! Your balance is getting heavy. Play another?",
                f"House loses this round. Don't let it get to your head."
            ])
        else:
            return random.choice([
                f"Number {w}. The math was definitely not on your side.",
                f"Another loss? The casino's new chandelier thanks you.",
                f"Ouch. That's gonna leave a dent in the bankroll."
            ])

class RegistrationWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Casino Registration")
        self.resize(350, 200)
        self.setStyleSheet("background-color: #0b0c10; color: #c5c6c7; font-size: 16px;")
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")
        self.name_input.setStyleSheet("background-color: #1f2833; color: #66fcf1; padding: 5px; border: 1px solid #45a29e;")
        
        self.balance_input = QDoubleSpinBox()
        self.balance_input.setRange(1.0, 1000000.0)
        self.balance_input.setValue(1000.0)
        self.balance_input.setPrefix("$ ")
        self.balance_input.setStyleSheet("background-color: #1f2833; color: #66fcf1; padding: 5px; border: 1px solid #45a29e;")
        
        start_btn = QPushButton("Start Game")
        start_btn.setStyleSheet("background-color: #45a29e; color: #0b0c10; font-weight: bold; padding: 10px; border-radius: 5px;")
        start_btn.clicked.connect(self.accept)

        form_layout = QFormLayout()
        form_layout.addRow("Player Name:", self.name_input)
        form_layout.addRow("Starting Balance:", self.balance_input)

        layout.addLayout(form_layout)
        layout.addStretch()
        layout.addWidget(start_btn)

    def get_data(self):
        name = self.name_input.text().strip() or "Player"
        balance = self.balance_input.value()
        return name, balance

class AppManager:
    def start(self):
        while True:
            reg = RegistrationWindow()
            if reg.exec() == QDialog.DialogCode.Accepted:
                name, balance = reg.get_data()
                db = MockDatabaseManager()
                controller = MockMainController(db, name, balance)
                window = CasinoGUI(controller, db)
                window.show()
                # Run event loop for this window
                QApplication.instance().exec()
                
                # Check if we should restart due to bankruptcy
                if not getattr(window, 'is_bankrupt', False):
                    break # Normal exit or window closed by user
            else:
                break # Cancelled registration

if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager = AppManager()
    manager.start()
    sys.exit()
