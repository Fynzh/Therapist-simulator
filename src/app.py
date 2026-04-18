import streamlit as st
import json
from pathlib import Path
from streamlit_option_menu import option_menu

def anti_none():
    if "in_work" not in st.session_state:
        st.session_state.in_work = False
    if "page" not in st.session_state:
        st.session_state.page = "menu"

# --- КОНФИГУРАЦИЯ ---
def init_paths() -> bool:
    # 1. Определяем базовую директорию
    current_dir = Path(__file__).resolve().parent
    base_dir = current_dir.parent if current_dir.name == "src" else current_dir
    data_dir = base_dir / "data"
    # 2. Определяем структуру папок
    paths = {
        "data": data_dir,
        "cases": data_dir / "cases",
        "media": data_dir / "media",
        "avatars": data_dir / "avatars",
        "users": data_dir / "users"
    }
    
    if "path" not in st.session_state:
        st.session_state.path = {}
    # 3. Проверяем наличие и сохраняем
    all_clear = True
    for key, path_obj in paths.items():
        if not path_obj.exists():
            st.error(f'❌ Критическая ошибка: Папка не найдена по пути: "{path_obj}"')
            all_clear = False
        else:
            # Сохраняем путь в session_state (например: st.session_state.data_path)
            st.session_state.path[f"{key}"] = path_obj
            
    return all_clear

def load_cases() -> dict:
    cases_dict = {}
    cases_path = st.session_state.path["cases"]

    # Проверяем, существует ли папка и является ли она директорией
    if not cases_path.is_dir():
        print(f"Ошибка: Путь {cases_path} не найден или не является папкой.")
        return cases_dict

    # Используем glob для фильтрации: файлы начинаются на case и заканчиваются на .json
    for file_path in cases_path.glob("case*.json"):
        try:
            # Path.read_text сам открывает и закрывает файл
            content = file_path.read_text(encoding='utf-8')
            data = json.loads(content)
            
            case_id = data.get("id")
            if case_id is not None:
                cases_dict[case_id] = {
                    "last_name": data.get("last_name"),
                    "first_name": data.get("first_name"),
                    "patronymic": data.get("patronymic"),
                    "age": data.get("age"),
                    "sex": data.get("sex"),
                    "answer": data.get("answer")
                }
        except (json.JSONDecodeError, OSError) as e:
            print(f"Ошибка при чтении файла {file_path.name}: {e}")

    return cases_dict

def load_case(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Ошибка чтения файла: {e}")
        return None

def sidebar_render():
    if st.session_state.page == "home":
        if st.sidebar.button("Кабинет", type="secondary", width="stretch", icon=":material/cases:"):
            st.session_state.page = "home"
            st.rerun()
    else:
        if st.sidebar.button("Кабинет", type="tertiary", width="stretch", icon=":material/cases:"):
            st.session_state.page = "home"
            st.rerun()
    if st.session_state.in_work == True:
        if st.session_state.page == "work":
            if st.sidebar.button("Приемная", type="secondary", width="stretch", icon=":material/person_alert:"):
                st.session_state.page = "work"
                st.rerun()
        else:
            if st.sidebar.button("Приемная", type="tertiary", width="stretch", icon=":material/person_alert:"):
                st.session_state.page = "work"
                st.rerun()
    if st.session_state.page == "settings":
        if st.sidebar.button("Настройки", type="secondary", width="stretch", icon=":material/settings:"):
            st.session_state.page = "settings"
            st.rerun()
    else:
        if st.sidebar.button("Настройки", type="tertiary", width="stretch", icon=":material/settings:"):
            st.session_state.page = "settings"
            st.rerun()
    if st.session_state.page == "stats":
        if st.sidebar.button("Статистика", type="secondary", width="stretch", icon=":material/query_stats:"):
            st.session_state.page = "stats"
            st.rerun()
    else:
        if st.sidebar.button("Статистика", type="tertiary", width="stretch", icon=":material/query_stats:"):
            st.session_state.page = "stats"
            st.rerun()
    if st.sidebar.button("Выйти", type="primary", width="stretch", icon=":material/close:"):
        st.session_state.clear()
        st.rerun()

# --- ГЛАВНАЯ ФУНКЦИЯ ---
def main():
    anti_none()
    if not init_paths():
        st.session_state.page = "error"
        render_error_page()
    if st.session_state.page == "error":
        render_error_page()
    sidebar_render()
    if st.session_state.page == "menu":
        render_menu_page()
    elif st.session_state.page == "home":
        render_home_page()
    elif st.session_state.page == "work":
        render_work_page()
    elif st.session_state.page == "settings":
        render_settings_page()
    elif st.session_state.page == "stats":
        render_stats_page()

def render_error_page():
    st.markdown("<h1 style='text-align: center;'>🚨 Системный сбой</h1>", unsafe_allow_html=True)
    
    st.divider()
    error_message = ""
    # Основной блок с пояснением
    st.error(f"""
    **Обнаружена критическая ошибка конфигурации среды.**
    
    Приложению не удалось получить доступ к необходимым ресурсам. Это может быть связано с отсутствием важных папок или повреждением структуры данных.
    """)

    # Инструкция для пользователя
    with st.container(border=True):
        st.markdown("""
        ### 🛠 Что делать?
        1. **Проверьте файлы:** Убедитесь, что папка `/data` существует в корневом каталоге проекта.
        2. **Перезапустите сервер:** Попробуйте остановить Streamlit (Ctrl+C в терминале) и запустить его снова.
        3. **Свяжитесь с разработчиком:** Если вы обычный пользователь, сообщите разработчику код ошибки выше.
        """)

    # Кнопка быстрой попытки перезапуска (просто обновит страницу)
    if st.button("Попробовать снова", icon=":material/refresh:", type="primary"):
        st.session_state.clear()
        st.rerun()

    st.info("Работа симулятора приостановлена для предотвращения повреждения базы данных пациентов.", icon=":material/lock:")
    st.stop()

def render_menu_page():
    st.title("Добро пожаловать!")
    st.title(":material/medical_services: Терапевтический симулятор")
    
    # Приветственный текст
    st.markdown("""
    ### Добро пожаловать в систему интерактивного обучения!
    
    Этот симулятор разработан для отработки навыков **клинического мышления**, сбора анамнеза и постановки диагноза. 
    Вы приступаете к работе в качестве дежурного врача приемного отделения.
    
    ---
    
    ### 🎯 Ваша задача:
    1.  **Собрать анамнез**: Выбирайте вопросы, чтобы уточнить жалобы и историю заболевания.
    2.  **Провести диагностику**: Назначайте необходимые лабораторные и инструментальные исследования.
    3.  **Поставить диагноз**: На основе собранных данных сформулируйте заключение.
    
    > **Помните:** Эффективность вашей работы оценивается по количеству и ценности заданных вопросов. Избегайте лишних исследований, чтобы сохранить ресурсы системы и время пациента.
    """)

    if st.button("Начать", type="primary"):
        st.session_state.page = "home"
        st.rerun()

    # Можно добавить визуальный разделитель и какие-то метрики/статусы
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Доступно кейсов", value="xxx")
    with col2:
        st.metric(label="Сложность", value="xxx")
    with col3:
        st.metric(label="Ваш статус", value="xxx")

def render_home_page():
    st.title("💼 Мой кабинет")
    st.markdown("### Выберите клинический случай")
    cases = load_cases()
    for id, case in cases.items():
        col1, col2 = st.columns([9, 1])
        with col1:
            if st.session_state.in_work == False:
                if st.button(
                    f"{id:<3} | {(f"{case['last_name']} {case['first_name'][0]}. {case["patronymic"][0]}."):^50} | {(str(case['age'])+" лет"):^30}".replace(" ", "\u00A0"),
                    width="content"
                ):
                    st.session_state.in_work = True
                    st.session_state.work_id = id
                    st.session_state.page = "work"
                    st.rerun()
            else:
                if st.button(
                    f"{id:<3} | {(f"{case['last_name']} {case['first_name'][0]}. {case["patronymic"][0]}."):^50} | {(str(case['age'])+" лет"):^30}".replace(" ", "\u00A0"),
                    width="content", 
                    disabled=True
                ):
                    pass
        with col2:
            st.markdown(f"0%")

def render_work_page():
    st.title(f"🩺 Ваш приемный кабинет ({st.session_state.work_id})")
    

    
    if st.button("Завершить работу (прогресс будет удален)", type="primary"):
        st.session_state.in_work = False
        st.session_state.page = "home"
        st.rerun()

def render_settings_page():
    st.title("⚙️ Настройки")
    st.write("Настройки интерфейса или сложности.")

def render_stats_page():
    st.title("📊 Статистика")
    st.write("Тут будет прогресс обучения студента.")

def render_patient_screen(data):
    """Отвечает только за отображение данных конкретного пациента."""
    st.title(f"Клинический случай: {data.get('patient_name', 'Неизвестный')}")
    
    with st.expander("📝 Анамнез", expanded=True):
        st.write(data.get('history', 'История отсутствует.'))

    # Инициализация сессии для чата
    case_key = f"chat_{data.get('id', 'default')}"
    if case_key not in st.session_state:
        st.session_state[case_key] = []

    # Логика вопросов
    st.divider()
    st.subheader("🗣️ Диалог")
    
    # Собираем вопросы
    questions = data.get('questions_id', {})
    all_q = questions.get('high', []) + questions.get('low', [])
    
    asked = [q['q'] for q in st.session_state[case_key]]
    available = [q['q'] for q in all_q if q['q'] not in asked]

    if available:
        col1, col2 = st.columns([3, 1])
        with col1:
            choice = st.selectbox("Задать вопрос:", ["-- Выберите --"] + available)
        with col2:
            st.write("") # Отступ
            if st.button("Спросить") and choice != "-- Выберите --":
                q_obj = next(q for q in all_q if q['q'] == choice)
                st.session_state[case_key].append(q_obj)
                st.rerun()
    
    # Отображение истории
    for chat in st.session_state[case_key]:
        with st.chat_message("user"):
            st.write(chat['q'])
        with st.chat_message("assistant"):
            st.write(chat['a'])

# Запуск программы
if __name__ == "__main__":
    main()