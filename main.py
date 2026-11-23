import pickle
from collections import UserDict
from datetime import datetime, date, timedelta
from functools import wraps


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        # Перевіряємо, що номер містить рівно 10 цифр
        if len(value) != 10 or not value.isascii() or not value.isdigit():
            raise ValueError("Phone number must contain exactly 10 digits.")

        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            birthday = datetime.strptime(value, "%d.%m.%Y")

            # Перевіряємо точну відповідність формату DD.MM.YYYY
            if birthday.strftime("%d.%m.%Y") != value:
                raise ValueError

        except (ValueError, TypeError):
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

        super().__init__(value)


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        # Додаємо новий телефон до списку
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        # Знаходимо та видаляємо телефон
        found_phone = self.find_phone(phone)

        if found_phone:
            self.phones.remove(found_phone)

    def edit_phone(self, old_phone, new_phone):
        # Перевіряємо, чи існує старий номер
        found_phone = self.find_phone(old_phone)

        if found_phone is None:
            raise ValueError("Phone number not found.")

        # Перевіряємо новий номер і замінюємо старий
        new_phone_obj = Phone(new_phone)
        index = self.phones.index(found_phone)
        self.phones[index] = new_phone_obj

    def find_phone(self, phone):
        # Шукаємо телефон за його значенням
        for phone_obj in self.phones:
            if phone_obj.value == phone:
                return phone_obj

        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        birthday = (
            str(self.birthday)
            if self.birthday is not None
            else "Not specified"
        )

        return (
            f"Contact name: {self.name.value}, "
            f"phones: {phones}, birthday: {birthday}"
        )


class AddressBook(UserDict):
    def add_record(self, record):
        # Зберігаємо запис, використовуючи ім'я як ключ
        self.data[record.name.value] = record

    def find(self, name):
        # Повертаємо запис або None, якщо його немає
        return self.data.get(name)

    def delete(self, name):
        # Видаляємо запис, якщо він існує
        self.data.pop(name, None)

    def get_upcoming_birthdays(self):
        today = date.today()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday = datetime.strptime(
                record.birthday.value, "%d.%m.%Y"
            ).date()

            def birthday_in_year(year):
                try:
                    return birthday.replace(year=year)
                except ValueError:
                    # 29 лютого у невисокосному році
                    return date(year, 2, 28)

            next_birthday = birthday_in_year(today.year)

            if next_birthday < today:
                next_birthday = birthday_in_year(today.year + 1)

            # Сьогодні + наступні 6 днів = 7 календарних днів
            days_until_birthday = (next_birthday - today).days

            if 0 <= days_until_birthday <= 6:
                congratulation_date = next_birthday

                # Переносимо привітання з вихідних на понеділок
                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                upcoming_birthdays.append({
                    "name": record.name.value,
                    "birthday": congratulation_date.strftime("%d.%m.%Y")
                })

        return upcoming_birthdays

    def __str__(self):
        # Формуємо рядок з усіх контактів
        return "\n".join(str(record) for record in self.data.values())


# Збереження адресної книги у файл
def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as file:
        pickle.dump(book, file)


# Завантаження адресної книги з файлу
def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter user name."
        except ValueError as error:
            return str(error) or "Give me name and phone please."

    return inner


def parse_input(user_input):
    if not user_input.strip():
        return "", []

    command, *args = user_input.split()
    return command.lower(), args


@input_error
def add_contact(args, book):
    name, phone = args
    record = book.find(name)

    if record is None:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return "Contact added."

    record.add_phone(phone)
    return "Contact updated."


@input_error
def change_contact(args, book):
    name, old_phone, new_phone = args
    record = book.find(name)

    if record is None:
        raise KeyError

    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)

    if record is None:
        raise KeyError

    if not record.phones:
        return "No phone numbers available."

    return "; ".join(str(phone) for phone in record.phones)


@input_error
def show_all(args, book):
    if not book.data:
        return "No contacts available."

    return str(book)


@input_error
def add_birthday(args, book):
    name, birthday = args
    record = book.find(name)

    if record is None:
        raise KeyError

    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)

    if record is None:
        raise KeyError

    if record.birthday is None:
        return "Birthday not specified."

    return str(record.birthday)


@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()

    if not upcoming:
        return "No upcoming birthdays."

    return "\n".join(
        f"{person['name']}: {person['birthday']}"
        for person in upcoming
    )


def main():
    # Відновлюємо адресну книгу з попереднього сеансу
    book = load_data()
    print("Welcome to the assistant bot!")

    try:
        while True:
            try:
                user_input = input("Enter a command: ")
            except (EOFError, KeyboardInterrupt):
                print("\nGood bye!")
                break

            command, args = parse_input(user_input)

            if command in ["close", "exit"]:
                print("Good bye!")
                break
            elif command == "hello":
                print("How can I help you?")
            elif command == "add":
                print(add_contact(args, book))
            elif command == "change":
                print(change_contact(args, book))
            elif command == "phone":
                print(show_phone(args, book))
            elif command == "all":
                print(show_all(args, book))
            elif command == "add-birthday":
                print(add_birthday(args, book))
            elif command == "show-birthday":
                print(show_birthday(args, book))
            elif command == "birthdays":
                print(birthdays(args, book))
            else:
                print("Invalid command.")
    finally:
        # Зберігаємо адресну книгу перед завершенням програми
        save_data(book)


if __name__ == "__main__":
    main()
