# FP
Final Project for CS32
67
Overview
67 is an interactive card game where players pick a number between 1–200, receive a hand of playing cards, and attempt to construct a mathematical expression that equals a target value using each card exactly once. The game is played using a text-based CLI with colorful terminal output for a retro gaming experience

The game automatically calculates hand size based on your number pick (higher picks → larger hands, increased difficulty) and provides optional hints by computing all valid mathematical expressions for your current hand.

How to Play
Pick a Number (1–200): Your pick determines your hand size:

Pick 1–67 → 4 cards
Pick 68–134 → 5 cards
Pick 135–200 → 6 cards


Build an Expression: Use each card value exactly once with the operators +, -, *, / to make 24.
Valid Operators: Only basic arithmetic operators are allowed:

Addition: +
Subtraction: -
Multiplication: * or x or ×
Division: /

Ex:
Cards [1, 2, 3, 4] → (1 + 2 + 3) * 4 = 24 ✓
Cards [6, 4, 4, 1] → 6 / (1 - 4/4) = 24 ✓

Scoring: Each correct solution adds 1 point to your score.


Installation & Setup
Requirements

Python 3.7+

No External Dependencies
67 uses only Python's standard library. No pip packages required
Running the Game
Terminal Version (Recommended for beginners)
bashpython3 GameRunner.py
This launches the colorful terminal interface with ASCII art cards.
Project Structure
67/
├── GameRunner.py              # Entry point for terminal version
├── terminal_game.py           # Terminal interface logic
├── validator.py               # Expression validation engine
├── solver.py                  # Solver for all valid expressions
├── deck.py                    # Card deck and hand utilities
├── constants.py               # Game constants (card values, etc.)
├── __init__.py                # Package initialization
└── README.md                  # This file

AI-Generated vs. Human-Written

AI Generated: Solver logic, color/formatting functions, validation error messages, overall code structure
Human Written: Game flow and loop logic, terminal/GUI interface design decisions, project organization, comments, and documentation

How AI Was Used
Claude was used in an iterative design process:

Initial specification of game rules and target features
Implementation of complex algorithms (solver, validator)
Styling and polish (terminal colors, card ASCII art)
Debugging and optimization suggestions
Code review and comment generation
