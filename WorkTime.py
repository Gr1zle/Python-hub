import threading
import time
import os
from datetime import datetime

# Глобальные переменные
user_data = {}  # Словарь для хранения данных пользователей (логин: {пароль, заметки})
current_user = None
last_activity_time = time.time()
license_duration = 30 * 60  # Лицензия на 30 минут (в секундах)
license_start_time = None
license_key = None

# Каталог для хранения пользовательских данных и логов
DATA_DIR = "user_data"
LOG_DIR = "logs"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Блокировки для потокобезопасности
user_data_lock = threading.Lock()
log_file_lock = threading.Lock()

# Функции для работы с файлами
def load_user_data():
    global user_data
    try:
        with open(os.path.join(DATA_DIR, "users.txt"), "r") as f:
            for line in f:
                login, password, notes = line.strip().split("|||")
                user_data[login] = {"password": password, "notes": notes}
        log_action(f"User data loaded from file.", "INFO")
    except FileNotFoundError:
        user_data = {}
        log_action(f"Файл с данными пользователей не найден. Создан новый.", "INFO")

def save_user_data():
    global user_data
    try:
        with open(os.path.join(DATA_DIR, "users.txt"), "w") as f:
            for login, data in user_data.items():
                f.write(f"{login}|||{data['password']}|||{data['notes']}\n")
        log_action(f"User data saved to file.", "INFO")
    except Exception as e:
        log_action(f"Ошибка при сохранении данных пользователей: {e}", "ERROR")

# Функции для логирования
def log_action(message, level="INFO"):
    global current_user
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    user = current_user if current_user else "System"
    log_message = f"[{level}] [{timestamp}] [{user}] - {message}\n"

    with log_file_lock:
        try:
            with open(os.path.join(LOG_DIR, "app.log"), "a") as f:
                f.write(log_message)
        except Exception as e:
            print(f"Ошибка при записи в лог: {e}")

# Функции для аутентификации и регистрации
def register_user(login, password):
    global user_data
    with user_data_lock:
        if login in user_data:
            return False, "Логин уже занят."
        user_data[login] = {"password": password, "notes": ""}
        save_user_data()
        log_action(f"New user registered: {login}", "INFO")
        return True, "Регистрация прошла успешно."

def authenticate_user(login, password):
    global user_data, current_user, license_start_time
    with user_data_lock:
        if login in user_data and user_data[login]["password"] == password:
            current_user = login
            license_start_time = time.time()
            log_action(f"User {login} successfully authenticated.", "INFO")
            return True, "Аутентификация прошла успешно."
        else:
            return False, "Неверный логин или пароль."

def get_user_notes(login):
    global user_data
    with user_data_lock:
        if login in user_data:
            return user_data[login]["notes"]
        else:
            return None

def save_user_notes(login, notes):
    global user_data
    with user_data_lock:
        if login in user_data:
            user_data[login]["notes"] = notes
            save_user_data()
            log_action(f"User {login}'s notes saved.", "INFO")
            return True
        else:
            return False

# Поток для автоматического сохранения заметок
def auto_save_thread():
    global current_user
    while True:
        if current_user:
            notes = get_user_notes(current_user)
            if notes:
              save_user_notes(current_user, notes)
        time.sleep(10)

# Поток для проверки активности пользователя
def activity_check_thread():
    global last_activity_time, current_user

    while True:
        time.sleep(60)
        if time.time() - last_activity_time > 60 and current_user:
            print("Пользователь не активен в течение минуты. Завершение работы.")
            log_action(f"User {current_user} was inactive. Exiting.", "INFO")
            os._exit(0)

# Поток для проверки лицензии
def license_check_thread():
    global license_start_time, current_user, license_duration
    while True:
        if current_user and license_start_time:
            time_elapsed = time.time() - license_start_time
            if time_elapsed > license_duration:
                print("Пробная лицензия программы завершена, чтобы продолжить работу приобретите лицензионный ключ!")
                log_action(f"User {current_user}'s license expired. Exiting.", "INFO")
                os._exit(0)
        time.sleep(60)

# Главная функция
def main():
    global last_activity_time, current_user

    load_user_data()

    # Запуск потоков
    threading.Thread(target=auto_save_thread, daemon=True).start()
    threading.Thread(target=activity_check_thread, daemon=True).start()
    threading.Thread(target=license_check_thread, daemon=True).start()

    while True:
        print("\n--- Меню ---")
        print("1. Регистрация") 
        print("2. Аутентификация")
        print("3. Просмотр/редактирование заметок")
        print("4. Выход")

        choice = input("Выберите действие: ")
        last_activity_time = time.time()

        if choice == "1":
            login = input("Введите логин: ")
            password = input("Введите пароль: ")
            success, message = register_user(login, password)
            print(message)
        elif choice == "2":
            login = input("Введите логин: ")
            password = input("Введите пароль: ")
            success, message = authenticate_user(login, password)
            print(message)
        elif choice == "3":
            if current_user:
                print("\n--- Ваши заметки ---")
                notes = get_user_notes(current_user)
                print(notes)
                new_notes = input("\nВведите новые заметки (или оставьте пустым для отмены): ")
                if new_notes:
                    save_user_notes(current_user, new_notes)
                    print("Заметки сохранены.")
                last_activity_time = time.time()

            else:
                print("Необходимо сначала аутентифицироваться.")
        elif choice == "4":
            print("Завершение работы...")
            log_action("Exiting program.", "INFO")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()