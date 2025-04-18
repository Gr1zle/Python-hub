import multiprocessing
import time
import os
import math
import psutil
from multiprocessing import Process, Queue, cpu_count

def caesar_cipher(text, shift, encrypt=True):
    result = []
    for char in text:
        if char.isalpha():
            shift_amount = shift if encrypt else -shift
            shifted = ord(char) + shift_amount
            if char.islower():
                if shifted > ord('z'):
                    shifted -= 26
                elif shifted < ord('a'):
                    shifted += 26
            elif char.isupper():
                if shifted > ord('Z'):
                    shifted -= 26
                elif shifted < ord('A'):
                    shifted += 26
            result.append(chr(shifted))
        else:
            result.append(char)
    return ''.join(result)

def worker(task_queue, result_queue, worker_id):
    while True:
        task = task_queue.get()
        if task is None:
            break
        
        part_num, text_part, shift, encrypt = task
        start_time = time.time()
        
        processed_text = caesar_cipher(text_part, shift, encrypt)
        process_time = time.time() - start_time
        
        result_queue.put((part_num, processed_text, worker_id, process_time))

def save_results(result_queue, output_file, total_parts):
    results = {}
    received_parts = 0
    
    while received_parts < total_parts:
        part_num, processed_text, worker_id, process_time = result_queue.get()
        results[part_num] = processed_text
        received_parts += 1
        
        print(f"Получена часть {part_num} от worker {worker_id} (время обработки: {process_time:.2f}s)")
    
    sorted_parts = [results[i] for i in sorted(results.keys())]
    final_text = ''.join(sorted_parts)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_text)
    
    print(f"Результат сохранен в файл: {output_file}")

def get_cpu_load():
    return psutil.cpu_percent(interval=1) / 100

def calculate_available_processes():
    total_cores = cpu_count()
    cpu_load = get_cpu_load()
    
    print(f"Текущая загрузка CPU: {cpu_load * 100:.1f}%")
    
    if cpu_load > 0.9:
        return max(1, total_cores // 4)
    elif cpu_load > 0.7:
        return max(1, total_cores // 2)
    elif cpu_load > 0.5:
        return max(1, int(total_cores * 0.75))
    else:
        return total_cores

def main():
    print("Файловый шифратор/дешифратор с мультипроцессингом")
    
    while True:
        mode = input("Выберите режим (1 - шифрование, 2 - дешифрование): ")
        if mode in ['1', '2']:
            encrypt = mode == '1'
            break
        print("Некорректный ввод. Попробуйте еще раз.")
    
    while True:
        file_path = input("Введите путь к файлу: ")
        if not os.path.exists(file_path):
            print("Файл не найден. Попробуйте еще раз.")
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            break
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                print("Не удалось прочитать файл. Поддерживаются только UTF-8 и CP1251 кодировки.")
    
    while True:
        shift_input = input("Введите сдвиг для шифра (по умолчанию 3): ")
        if not shift_input:
            shift = 3
            break
        try:
            shift = int(shift_input)
            break
        except ValueError:
            print("Некорректный сдвиг. Попробуйте еще раз.")
    
    available_processes = calculate_available_processes()
    total_cores = cpu_count()
    
    print(f"Доступно ядер CPU: {total_cores}")
    print(f"Рекомендуемое количество процессов: {available_processes}")
    
    while True:
        processes_input = input(
            f"Введите количество процессов (1-{available_processes}): ")
        if not processes_input:
            num_processes = available_processes
            break
        try:
            num_processes = int(processes_input)
            if 1 <= num_processes <= available_processes:
                break
            print(f"Число должно быть от 1 до {available_processes}")
        except ValueError:
            print("Некорректный ввод. Попробуйте еще раз.")

    chunk_size = max(1, math.ceil(len(text) / num_processes))
    parts = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    task_queue = Queue()
    result_queue = Queue()

    for i, part in enumerate(parts):
        task_queue.put((i, part, shift, encrypt))

    for _ in range(num_processes):
        task_queue.put(None)

    workers = []
    for i in range(num_processes):
        p = Process(target=worker, args=(task_queue, result_queue, i))
        workers.append(p)
        p.start()

    timestamp = int(time.time())
    output_file = f"{'encrypted' if encrypt else 'decrypted'}_{timestamp}.txt"
    saver = Process(target=save_results, args=(result_queue, output_file, len(parts)))
    saver.start()

    for p in workers:
        p.join()
    
    saver.join()
    
    print("Обработка завершена! :)")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()