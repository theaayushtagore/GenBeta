import os
import random
import requests
import csv
import telebot
import re  
from datetime import datetime
from telebot import types

# Replace this with your bot token
BOT_TOKEN = "7923483065:AAFykrRqcrHBUKm2-5Hjy6smIfgo1suhvbQ"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="html")

# BIN Data URL
BIN_DATA_URL = "https://raw.githubusercontent.com/venelinkochev/bin-list-data/master/bin-list-data.csv"

# Function to fetch BIN details from the CSV file
def get_bin_info(bin_number):
    try:
        response = requests.get(BIN_DATA_URL)
        if response.status_code != 200:
            return None

        bin_data = response.text.splitlines()
        reader = csv.reader(bin_data)

        for row in reader:
            if row and row[0].startswith(bin_number):  # Match first 6 digits
                return {
                    "BIN": row[0],
                    "Type": row[1],
                    "Category": row[2],
                    "Bank": row[4],
                    "Country": row[7],
                    "Country_Name": row[8]
                }
        return None  
    except Exception as e:
        return None

# Luhn algorithm to generate a valid 16-digit card number
def generate_valid_card(bin_prefix):
    while True:
        card_number = list(bin_prefix) + [str(random.randint(0, 9)) for _ in range(16 - len(bin_prefix) - 1)]
        check_digit = get_luhn_check_digit(card_number)
        card_number.append(str(check_digit))
        return "".join(card_number)

# Luhn check digit calculator
def get_luhn_check_digit(digits):
    digits = [int(d) for d in digits]
    for i in range(len(digits) - 1, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    return (10 - sum(digits) % 10) % 10

# Function to generate valid credit cards
def generate_credit_cards(bin_input, amount=10):
    cards = []
    current_year = datetime.now().year

    # Extract BIN and optional details
    parts = bin_input.split("|")
    bin_number = re.sub(r"\D", "", parts[0].strip())[:6]  # Extract only first 6 digits
    
    # Use the full input for card generation
    full_bin_number = re.sub(r"\D", "", parts[0].strip())  # Get the full input without non-digits

    fixed_exp_month = parts[1] if len(parts) > 1 and parts[1].isdigit() and 1 <= int(parts[1]) <= 12 else None
    fixed_exp_year = parts[2] if len(parts) > 2 and parts[2].isdigit() and int(parts[2]) >= current_year else None
    fixed_cvv = parts[3] if len(parts) > 3 and parts[3].isdigit() and len(parts[3]) in [3, 4] else None

    for _ in range(amount):
        card_number = generate_valid_card(full_bin_number)  # Use full_bin_number for card generation

        # Generate random expiry and CVV if not provided
        exp_month = fixed_exp_month if fixed_exp_month else str(random.randint(1, 12)).zfill(2)
        exp_year = fixed_exp_year if fixed_exp_year else str(random.randint(current_year + 1, current_year + 5))
        cvv = fixed_cvv if fixed_cvv else str(random.randint(100, 999))  

        cards.append(f"{card_number}|{exp_month}|{exp_year}|{cvv}")
    
    return cards

# Welcome Message Handler
@bot.message_handler(commands=['start'])
def welcome_message(message):
    welcome_text = f"""
🎉 <b>Welcome to the BIN & CC Generator Bot!</b> 🚀

🔥 <b>Features:</b>
  ✅ Check BIN details (Bank, Country, Type) 🏦
  ✅ Generate valid CC details for testing 💳
  ✅ Fast and accurate responses ⚡

📌 <b>How to Use:</b>
  🎯 <code>/gen &lt;BIN&gt;</code> - Generate CC details from a BIN
     🔹 Example: <code>/gen 414734</code>
  🎯 <code>/gen &lt;BIN&gt;|MM|YYYY|CVV</code> - Use custom expiry & CVV
     🔹 Example: <code>/gen 546775904267xxxx|03|2028|999</code>

⚠️ <b>Disclaimer:</b>
This bot is for <b>educational and testing purposes only</b>.
Misuse for fraud is strictly prohibited. ❌

⚡ <b>Start by entering a command now!</b>
"""
    bot.reply_to(message, welcome_text, parse_mode="html")

# Command handler for /gen and .gen
@bot.message_handler(func=lambda message: message.text.startswith('/gen') or message.text.startswith('.gen'))
def generate_handler(message):
    try:
        text = message.text.split(" ")
        if len(text) < 2:
            bot.reply_to(message, "⚠️ Please enter a BIN.\nExample: <code>/gen 414734</code>", parse_mode="html")
            return

        bin_input = text[1].strip()
        bin_number = re.sub(r"\D", "", bin_input)[:6]

        # Get BIN information
        bin_info = get_bin_info(bin_number)
        if not bin_info:
            bot.reply_to(message, "❌ BIN not found in the database.", parse_mode="html")
            return

        cards = generate_credit_cards(bin_input)

        response = f"""
━━━━━━━━━━━━━━━━━━
💳 <b>BIN:</b> {bin_info['BIN']}  
🏦 <b>Type:</b> {bin_info['Type']}  
🏷️ <b>Category:</b> {bin_info['Category']}  
🏛️ <b>Bank:</b> {bin_info['Bank']}  
🌍 <b>Country:</b> {bin_info['Country']} ({bin_info['Country_Name']})  
📦 <b>Amount:</b> {len(cards)}  
━━━━━━━━━━━━━━━━━━
"""

        for card in cards:
            response += f"<code>{card}</code>\n"

        bot.reply_to(message, response, parse_mode="html")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}", parse_mode="html")

# Start the bot
bot.infinity_polling()