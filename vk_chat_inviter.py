import vk_api
import time
import random
import os
import webbrowser
import urllib.parse
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.exceptions import ApiError
from vk_api.utils import get_random_id
import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

# --- НАСТРОЙКИ ПРОГИ ---
TOKEN_FILE = 'vk_token.txt'
ADDED_USERS_FILE = 'added_users.txt'  # Файл для хранения ID пользователей типо мол - которые уже были добавлены.
GROUP_IDS = ['reallyworld'] # Замените на ID групп допустим (['reallyworld', 'group_id_2', 'group_id_3']) ну ты пон)
CHAT_ID = 2000000089  # ID вашего чата
MESSAGE_TO_SEND = "Привет! У нас новый проект https://t.me/VeilRises. Открытие 5 апреля. Присоединяйся!" # Текст который будет писаться челам в лс.
USERS_PER_CYCLE = 5 # Сколько людей за один цикл будет добавлено в чат.
DELAY_SECONDS = 5 # Сколько секунд программа будет ждать перед следующим циклом.

APP_ID = 2685278 # Я использовал Kate Mobile лишь чтобы получить токен. А так можно использовавать любое приложение.
REDIRECT_URI = 'https://oauth.vk.com/blank.html'

# КОД ПРОГИ Тут я расписал каждую функцию для удобства ренейма.

# Получение токена из файла token.txt
def get_token_from_file():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            token = f.read().strip()
            if token:
                return token
    return None

#Сохранение токена в файл token.txt
def save_token_to_file(token):
    with open(TOKEN_FILE, 'w') as f:
        f.write(token)
    print(f"{Fore.GREEN}Токен сохранен в файл {TOKEN_FILE}")

# Получение списка уже добавленных пользователей из файла added_users.txt
def get_added_users():
    added_users = set()
    if os.path.exists(ADDED_USERS_FILE):
        with open(ADDED_USERS_FILE, 'r') as f:
            for line in f:
                user_id = line.strip()
                if user_id and user_id.isdigit():
                    added_users.add(int(user_id))
    return added_users

# Сдесь идёт сохранение ID пользователя в файл added_users.txt
def save_added_user(user_id):
    with open(ADDED_USERS_FILE, 'a') as f:
        f.write(f"{user_id}\n")
    print(f"{Fore.CYAN}Пользователь ID {user_id} сохранен в истории добавлений")

# Сдесь идёт получение токена.
def get_auth_token():
    token = get_token_from_file()
    if token:
        print(f"{Fore.BLUE}Найден сохраненный токен.")
        try:
            vk_session = vk_api.VkApi(token=token)
            vk_session.get_api().users.get()
            print(f"{Fore.GREEN}Токен валиден.")
            return token
        except:
            print(f"{Fore.RED}Сохраненный токен недействителен. Необходима повторная авторизация.")
    
    # Сдесь идёт генерация ссылки для авторизации.
    auth_url = f"https://oauth.vk.com/authorize?" + urllib.parse.urlencode({
        'client_id': APP_ID,
        'display': 'page',
        'redirect_uri': REDIRECT_URI,
        'scope': 'friends,photos,audio,video,docs,notes,pages,status,wall,groups,messages,notifications,stats,offline',
        'response_type': 'token',
        'revoke': '1',
        'v': '5.131'
    })
    
    print(f"\n{Fore.YELLOW}{Back.BLUE}{Style.BRIGHT}=== Получение токена ==={Style.RESET_ALL}")
    print(f"{Fore.CYAN}1. Сейчас откроется ссылка в браузере: {Fore.BLUE}{auth_url}")
    print(f"{Fore.CYAN}2. Войдите в свой аккаунт ВКонтакте.")
    print(f"{Fore.CYAN}3. Разрешите доступ приложению")
    print(f"{Fore.CYAN}4. После разрешения вас перенаправит на страницу, где в адресной строке будет токен")
    print(f"{Fore.CYAN}   В адресной строке найдите часть после 'access_token=' и до символа '&'")
    print(f"{Fore.CYAN}   Например, из 'https://oauth.vk.com/blank.html#access_token=abcdef123456&expires_in=0&user_id=123456'")
    print(f"{Fore.CYAN}   нужно скопировать только 'abcdef123456'")
    print(f"{Fore.CYAN}   Надеюсь ты пон.)")
    

    #Тут вызываем функцию для открытия браузера. И проверяем на ошибки.
    try:
        webbrowser.open(auth_url)
    except:
        print(f"\n{Fore.RED}Не удалось открыть браузер автоматически. Пожалуйста, скопируйте и откройте следующую ссылку вручную:")
        print(f"{Fore.BLUE}{auth_url}")
    
    print(f"\n{Fore.YELLOW}После авторизации в браузере, скопируйте токен и вставьте его сюда:")
    token = input(f"{Fore.GREEN}Вставьте токен доступа: {Style.RESET_ALL}").strip()
    
    if not token:
        print(f"{Fore.RED}Токен не был введен. Авторизация не удалась.")
        return None
    
    # Проверяем валидность полученного токена
    try:
        vk_session = vk_api.VkApi(token=token)
        vk_session.get_api().users.get()
        print(f"{Fore.GREEN}Токен валиден. Авторизация успешна!")
        save_token_to_file(token)
        return token
    except Exception as e:
        print(f"{Fore.RED}Ошибка при проверке токена: {e}")
        return None

# Сдесь идёт проверка на админа из групп.
def check_if_admin(vk, group_id, user_id):
    try:
        if not group_id.startswith('-') and not group_id.isdigit():
            group_info = vk.utils.resolveScreenName(screen_name=group_id)
            if group_info and group_info['type'] == 'group':
                group_id = group_info['object_id']
            else:
                return False
        elif group_id.startswith('-'):
            group_id = group_id[1:]

        try:
            member_info = vk.groups.getMembers(
                group_id=group_id,
                filter='managers'
            )
            
            # Проверка есть ли пользователь в списке администраторов.
            admin_ids = [item['id'] for item in member_info.get('items', [])]
            return user_id in admin_ids
        except ApiError as e:
            if "Access denied: group hide members" in str(e):
                # Если группа скрывает участников - считаем что пользователь не админ
                print(f"{Fore.YELLOW}Группа {group_id} скрывает список участников. Пропускаем проверку админов.")
                return False
            raise
    except Exception as e:
        print(f"{Fore.RED}Ошибка при проверке администратора: {e}")
        return False  # В случае ошибки считаем, что пользователь не админ ) хаха

# Сдесь идёт основная функция проги. И куча проверок ...
def main():
    # Выводим приветствие и информацию о программе
    print(f"{Fore.CYAN}{Back.BLACK}{Style.BRIGHT}{'=' * 60}")
    print(f"{Fore.YELLOW}{Back.BLACK}{Style.BRIGHT}  VK ЧАТ ИНВАЙТЕР - ПРИГЛАШЕНИЕ ПОЛЬЗОВАТЕЛЕЙ В БЕСЕДУ  ")
    print(f"{Fore.CYAN}{Back.BLACK}{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")
    
    # Получаем токен
    token = get_auth_token()
    if not token:
        print(f"{Fore.RED}Не удалось получить токен. Программа завершается.")
        return
    
    try:
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        print(f"{Fore.GREEN}Авторизация прошла успешно.")
        
        # Получаем информацию о текущем пользователе
        user_info = vk.users.get()[0]
        print(f"{Fore.CYAN}Работаем от имени: {Fore.WHITE}{Style.BRIGHT}{user_info['first_name']} {user_info['last_name']}")
    except ApiError as e:
        print(f"{Fore.RED}Ошибка авторизации VK API: {e}")
        return
    except Exception as e:
        print(f"{Fore.RED}Непредвиденная ошибка при авторизации: {e}")
        return

    # Загружаем список добавленных пользователей
    added_users = get_added_users()
    print(f"{Fore.BLUE}Загружен список уже добавленных пользователей: {len(added_users)} чел.")

    # Выводим информацию о настройках
    print(f"\n{Fore.YELLOW}{Back.BLUE}{Style.BRIGHT} ТЕКУЩИЕ НАСТРОЙКИ {Style.RESET_ALL}")
    print(f"{Fore.CYAN}Группы для поиска: {Fore.WHITE}{', '.join(GROUP_IDS)}")
    print(f"{Fore.CYAN}ID чата: {Fore.WHITE}{CHAT_ID}")
    print(f"{Fore.CYAN}Пользователей за цикл: {Fore.WHITE}{USERS_PER_CYCLE}")
    print(f"{Fore.CYAN}Задержка между циклами: {Fore.WHITE}{DELAY_SECONDS} сек.")
    print(f"{Fore.CYAN}Сообщение для отправки: {Fore.WHITE}\"{MESSAGE_TO_SEND}\"")
    
    processed_users_current_cycle = 0
    users_to_add = []

    cycle_count = 1
    while True:
        print(f"\n{Fore.YELLOW}{Back.BLACK}{Style.BRIGHT}----- Цикл #{cycle_count} ({time.strftime('%Y-%m-%d %H:%M:%S')}) -----{Style.RESET_ALL}")
        processed_users_current_cycle = 0
        users_to_add.clear()

        for group_id in GROUP_IDS:
            if processed_users_current_cycle >= USERS_PER_CYCLE:
                print(f"{Fore.YELLOW}Достигнут лимит пользователей за цикл.")
                break

            print(f"{Fore.BLUE}Обработка группы: {Fore.WHITE}{group_id}")
            try:
                target_id = group_id
                if not group_id.startswith('-') and not group_id.isdigit():
                    group_info = vk.utils.resolveScreenName(screen_name=group_id)
                    if group_info and group_info['type'] == 'group':
                         target_id = -group_info['object_id']
                    elif group_info and group_info['type'] == 'page':
                         target_id = group_info['object_id']
                    else:
                        print(f"{Fore.RED}Не удалось определить ID для {group_id}")
                        continue
                elif group_id.startswith('-') and group_id[1:].isdigit():
                    target_id = int(group_id)
                elif group_id.isdigit():
                     print(f"{Fore.YELLOW}Предупреждение: используется числовой ID {group_id} без знака '-' для группы/паблика.")
                     target_id = int(group_id)

                # Получаем последних постов со стены
                wall = vk.wall.get(owner_id=target_id, count=5)
                if not wall['items']:
                    print(f"{Fore.YELLOW}Нет постов для обработки.")
                    continue

                for post in wall['items']:
                    post_id = post['id']
                    print(f"{Fore.CYAN}Обработка поста: ID {post_id}")

                    # Получаем комментарии к посту
                    try:
                        comments = vk.wall.getComments(owner_id=target_id, post_id=post_id, count=100, sort='desc', thread_items_count=0)
                    except ApiError as e:
                        print(f"{Fore.RED}Ошибка при получении комментариев к посту {post_id}: {e}")
                        continue

                    if not comments['items']:
                        print(f"{Fore.YELLOW}Нет комментариев к посту.")
                        continue

                    print(f"{Fore.GREEN}Найдено комментариев: {comments['count']}")

                    commenter_ids = list(set(comment['from_id'] for comment in comments['items'] if comment['from_id'] > 0))
                    random.shuffle(commenter_ids)

                    if not commenter_ids:
                         print(f"{Fore.YELLOW}Нет подходящих комментаторов.")
                         continue

                    users_info = vk.users.get(user_ids=commenter_ids, fields="can_write_private_message")

                    for user in users_info:
                        if processed_users_current_cycle >= USERS_PER_CYCLE:
                            print(f"{Fore.YELLOW}Достигнут лимит пользователей за цикл.")
                            break

                        user_id = user['id']
                        
                        # Проверяем, не добавляли ли мы уже этого пользователя ранее
                        if user_id in added_users:
                            print(f"{Fore.YELLOW}  -> Пользователь ID {user_id} уже был добавлен ранее. Пропускаем.")
                            continue
                        
                        # Проверяем, не админ ли это
                        if check_if_admin(vk, group_id, user_id):
                            print(f"{Fore.YELLOW}  -> Пользователь ID {user_id} является администратором группы. Пропускаем.")
                            # Добавляем админа в список добавленных, чтобы больше не проверять
                            added_users.add(user_id)
                            save_added_user(user_id)
                            continue
                        
                        can_write = user.get('can_write_private_message', False)

                        if can_write:
                            if user_id not in users_to_add:
                                print(f"{Fore.GREEN}  -> Найден подходящий пользователь: ID {user_id}")
                                users_to_add.append(user_id)
                                processed_users_current_cycle += 1
                            else:
                                print(f"{Fore.YELLOW}  -> Пользователь ID {user_id} уже в списке на добавление.")
                        else:
                            print(f"{Fore.RED}  -> Пользователю ID {user_id} нельзя написать сообщение. Сохраняем в историю.")
                            added_users.add(user_id)
                            save_added_user(user_id)


                        #Заканчиваем цикл.
                        if processed_users_current_cycle >= USERS_PER_CYCLE:
                            break

            except ApiError as e:
                print(f"{Fore.RED}Ошибка VK API при обработке группы {group_id}: {e}")
                time.sleep(5)
            except Exception as e:
                print(f"{Fore.RED}Непредвиденная ошибка при обработке группы {group_id}: {e}")
                time.sleep(5)

        # Отправляем сообщения и добавляем в чат
        if users_to_add:
            print(f"\n{Fore.YELLOW}{Back.BLUE}{Style.BRIGHT} Отправка сообщений и добавление в чат ({len(users_to_add)} пользователей) {Style.RESET_ALL}")
            for i, user_id in enumerate(users_to_add):
                try:
                    print(f"{Fore.CYAN}[{i+1}/{len(users_to_add)}] Обработка пользователя ID {user_id}")
                    
                    # 1. Отправка сообщения
                    message_sent = False
                    try:
                        vk.messages.send(
                            user_id=user_id,
                            message=MESSAGE_TO_SEND,
                            random_id=get_random_id()
                        )
                        print(f"{Fore.GREEN}  ✓ Сообщение отправлено пользователю ID {user_id}")
                        message_sent = True
                        time.sleep(random.uniform(1, 3))
                    except ApiError as e:
                        print(f"{Fore.RED}  ✗ Ошибка при отправке сообщения пользователю ID {user_id}: {e}")
                        # Если пользователь в черном списке или другая ошибка
                        if "Can't send messages for users from blacklist" in str(e):
                            print(f"{Fore.YELLOW}  → Пользователь ID {user_id} в черном списке. Сохраняем в историю и пропускаем.")
                            added_users.add(user_id)
                            save_added_user(user_id)
                            continue

                    # 2. Добавление в чат только если сообщение отправлено успешно
                    if message_sent:
                        try:
                            vk.messages.addChatUser(
                                chat_id=CHAT_ID - 2000000000,
                                user_id=user_id
                            )
                            print(f"{Fore.GREEN}  ✓ Пользователь ID {user_id} добавлен в чат {CHAT_ID}")
                        except ApiError as e:
                            print(f"{Fore.RED}  ✗ Ошибка при добавлении пользователя ID {user_id} в чат: {e}")
                    
                    added_users.add(user_id)
                    save_added_user(user_id)
                    
                    time.sleep(random.uniform(1, 3))

                except Exception as e:
                    print(f"{Fore.RED}Непредвиденная ошибка при обработке пользователя ID {user_id}: {e}")
                    added_users.add(user_id)
                    save_added_user(user_id)

        else:
            print(f"{Fore.YELLOW}Нет пользователей для добавления в этом цикле.")

        print(f"\n{Fore.CYAN}{Back.BLACK}{Style.BRIGHT}----- Цикл #{cycle_count} завершен. Ожидание {DELAY_SECONDS / 60:.1f} минут... -----{Style.RESET_ALL}")
        cycle_count += 1
        # Обратный отсчет
        wait_time = DELAY_SECONDS
        while wait_time > 0:
            mins, secs = divmod(wait_time, 60)
            timer = f"{int(mins):02d}:{int(secs):02d}"
            print(f"{Fore.CYAN}До следующего цикла: {timer}", end="\r")
            time.sleep(1)
            wait_time -= 1

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}{Back.RED}{Style.BRIGHT} Программа остановлена пользователем {Style.RESET_ALL}")
    except Exception as e:
        print(f"\n\n{Fore.RED}{Back.BLACK}{Style.BRIGHT} Критическая ошибка: {e} {Style.RESET_ALL}")