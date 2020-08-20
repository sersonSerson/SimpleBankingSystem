import random
import sqlite3
import os


class CreditCard:
    BIN = '400000'
    current_account = None

    def __init__(self, card_id=0, number='', pin='', balance=0, new=True):
        if new:
            self.number = self.generate_number()
            self.card_id = int(self.number)
            self.pin = self.generate_pin()
            self.balance = 0
            DatabaseConnection().create_card(self)
        else:
            self.number = number
            self.card_id = int(card_id)
            self.pin = pin
            self.balance = balance

    def get_balance(self):
        balance = DatabaseConnection().get_balance(self)
        self.balance = balance
        return balance

    def get_number(self):
        return self.number

    def get_pin(self):
        return self.pin

    def get_id(self):
        return self.card_id

    def update_balance(self, balance_update):
        self.balance += balance_update
        DatabaseConnection().update_balance(self, balance_update)

    @staticmethod
    def update_current_account(account):
        CreditCard.current_account = account

    @staticmethod
    def generate_number():
        number = str(random.randint(1, 1000000000))

        while len(number) < 9:
            number += '0'
        number = CreditCard.BIN + number
        number = CreditCard.add_checksum(number)

        return number

    @staticmethod
    def generate_pin():
        random_pin = str(random.randint(1, 10000))
        while len(random_pin) < 4:
            random_pin += '0'
        return random_pin

    @staticmethod
    def luhn_sum(number):
        lunh = int()
        for i in range(0, 15):
            value = int(number[i])
            if (i + 1) % 2 == 1:
                # For odd numbers multiply by 2
                value *= 2
            if value >= 10:
                # Decrease values over 10 by nine
                value -= 9
            lunh += value

        return lunh

    @staticmethod
    def add_checksum(number):
        remainder = CreditCard.luhn_sum(number) % 10
        if remainder != 0:
            last_digit = str(10 - remainder)
        else:
            last_digit = '0'
        number += last_digit
        return number

    @staticmethod
    def luhn_correct(number):
        luhn_sum = CreditCard.luhn_sum(number)
        if (luhn_sum + int(number[-1])) % 10 == 0:
            return True
        else:
            return False


class Menu:
    show = True

    @staticmethod
    def menu():
        while Menu.show:
            if CreditCard.current_account:
                Menu.logged_in_menu()
            else:
                Menu.main_menu()
            print()

    @staticmethod
    def main_menu():
        print('1. Create an account\n',
              '2. Log into account\n',
              '0. Exit', sep='')
        user = Menu.user_input()
        if user == 1:
            card = CreditCard()
            print('Your card has been created', 'Your card number:',
                  card.number, 'Your card PIN:', card.pin, sep='\n')
        elif user == 2:
            print('Enter your card number:')
            number = Menu.user_input()
            print('Enter your PIN:')
            pin = Menu.user_input()
            DatabaseConnection().login(number, pin)
            if CreditCard.current_account:
                print('You have successfully logged in!')
            else:
                print('Wrong card number or PIN!')
        if user == 0:
            print('Bye!')
            Menu.show = False

    @staticmethod
    def logged_in_menu():
        print('1. Balance\n',
              '2. Add income\n',
              '3. Do transfer\n',
              '4. Close account\n',
              '5. Log out\n',
              '0. Exit', sep='')
        user = Menu.user_input()
        if user == 1:
            Menu.print_balance()
        elif user == 2:
            print("Enter income:")
            CreditCard.current_account.update_balance(Menu.user_input())
            print("Income was added!")
        elif user == 3:
            print('Transfer'),
            print('Enter card number:')
            receiver_number = str(Menu.user_input())
            if not CreditCard.luhn_correct(receiver_number):
                print('Probably you made mistake in the card number. Please try again!')

            else:
                if receiver_number == CreditCard.current_account.get_number():
                    print('You can\'t transfer money to the same account!')
                else:
                    reciever_card_data = DatabaseConnection().card_data(receiver_number)
                    if reciever_card_data is None:
                        print('Such a card does not exist.')
                print('Enter how much money you want to transfer:')
                transfer = Menu.user_input()
                if transfer > CreditCard.current_account.get_balance():
                    print("Not enough money!")
                else:
                    reciever_card = CreditCard(*reciever_card_data, new=False)
                    CreditCard.current_account.update_balance(-transfer)
                    reciever_card.update_balance(transfer)
                    print('Success!')
                
        elif user == 4:
            DatabaseConnection().remove_card(CreditCard.current_account)
            CreditCard.update_current_account(None)
        elif user == 5:
            CreditCard.update_current_account(None)
        elif user == 0:
            Menu.show = False

    @staticmethod
    def print_balance():
        print('Balance:', DatabaseConnection().get_balance(CreditCard.current_account))

    @staticmethod
    def user_input():
        return int(input())


class DatabaseConnection:

    # connection = DatabaseConnection('card.s3db')
    def __init__(self, path='card.s3db'):
        table_exists = False
        if os.path.exists(path):
            table_exists = True
        self.connection = sqlite3.connect(path)

        if not table_exists:
            self.create_table()

    def create_table(self):

        cur = self.connection.cursor()
        cur.execute('CREATE TABLE card ('
                    'id INTEGER,'
                    'number TEXT,'
                    'pin TEXT,'
                    'balance INTEGER);')
        self.connection.commit()

    def card_data(self, number):
        cur = self.connection.cursor()
        result = cur.execute(f'SELECT id, number, pin, balance  FROM card WHERE id = {number};').fetchone()
        self.connection.close()
        return result

    def login(self, number, pin):
        card_data = self.card_data(number)
        if not card_data:
            return None
        correct_pin = card_data[2]
        if str(pin) == correct_pin:
            CreditCard.update_current_account(CreditCard(*card_data, new=False))


    def update_balance(self, card, balance_update):

        cur = self.connection.cursor()
        cur.execute(f'UPDATE card SET balance=balance + {balance_update} WHERE id = {card.get_id()};')
        self.connection.commit()

    def get_balance(self, card):
        cur = self.connection.cursor()
        result = cur.execute(f'SELECT balance FROM card WHERE id = {card.get_id()};').fetchone()
        self.connection.close()
        if result is None:
            return 0
        else:
            return result[0]

    def create_card(self, card):

        cur = self.connection.cursor()
        cur.execute(f'INSERT INTO card (id, number, pin, balance) VALUES  '
                    f'({card.get_id()}, {card.get_number()}, '
                    f'{card.get_pin()}, 0);')
        self.connection.commit()

    def remove_card(self, card):
        cur = self.connection.cursor()
        cur.execute(f'DELETE FROM card WHERE id = {card.get_id()};')
        self.connection.commit()


# connection = DatabaseConnection('card.s3db')
Menu.menu()
