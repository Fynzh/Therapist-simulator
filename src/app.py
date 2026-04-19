import streamlit as st
import json
from pathlib import Path
from streamlit_option_menu import option_menu

def anti_none():
    defaults = {
        "in_work": False,
        "page": "menu",
        "n": 0,
        "n_change": True,
        "excluded_q": [],
        "work_id": None,
        "path" : {},
        #"stage": "questions",
        #"ordered_exams": [],
        #"user_diagnosis": "",
        "stats": {},
        #"last_stat_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_work_state():
    st.session_state.excluded_q = []
    st.session_state.n = 0
    st.session_state.n_change = True
    #st.session_state.stage = "questions"
    #st.session_state.ordered_exams = []
    #st.session_state.user_diagnosis = ""
    st.session_state.in_work = False
    st.session_state.work_id = None
    if "dialog" in st.session_state:
        del st.session_state["dialog"]

def init_paths() -> bool:
    current_dir = Path(__file__).resolve().parent
    base_dir = current_dir.parent if current_dir.name == "src" else current_dir
    data_dir = base_dir / "data"
    paths = {
        "data": data_dir,
        "cases": data_dir / "cases",
        "media": data_dir / "media",
        "avatars": data_dir / "avatars",
        "users": data_dir / "users"
    }
    all_clear = True
    for key, path_obj in paths.items():
        if not path_obj.exists():
            st.error(f'❌ Критическая ошибка: Папка не найдена по пути: "{path_obj}"')
            all_clear = False
        else:
            st.session_state.path[f"{key}"] = path_obj
            
    return all_clear

def load_cases() -> dict:
    cases_dict = {}
    cases_path = st.session_state.path["cases"]
    if not cases_path.is_dir():
        print(f"Ошибка: Путь {cases_path} не найден или не является папкой.")
        return cases_dict
    for file_path in sorted(cases_path.glob("case*.json")):
        try:
            data = json.loads(file_path.read_text(encoding='utf-8'))
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

def get_top_questions(questions, limit=3):
    sorted_questions = sorted(questions, key=lambda x: x[1].get('weight', 0), reverse=True)
    return {
        orig_id: {
            "q": item["q"],
            "a": item["a"],
            "weight": item["weight"]
        }
        for orig_id, item in sorted_questions[:limit]
    }

def calculate_score(case, asked_ids):
    total = sum(q["weight"] for q in case["questions"] if q.get("weight", 0) > 0)
    user_weight = sum(case['questions'][q_id]['weight'] for q_id in asked_ids)
    if total == 0:
        return 0
    return round((user_weight / total) * 100)

def sidebar_render():
    btn = lambda active: "secondary" if active else "tertiary"
    if st.sidebar.button("Кабинет", type=btn(st.session_state.page == "home"),
                         width="stretch", icon=":material/cases:"):
        st.session_state.page = "home"
        st.rerun()
    if st.session_state.in_work:
        if st.sidebar.button("Приёмная", type=btn(st.session_state.page == "work"),
                             width="stretch", icon=":material/person_alert:"):
            st.session_state.page = "work"
            st.rerun()
    if st.sidebar.button("Настройки", type=btn(st.session_state.page == "settings"),
                         width="stretch", icon=":material/settings:"):
        st.session_state.page = "settings"
        st.rerun()
    if st.sidebar.button("Статистика", type=btn(st.session_state.page == "stats"),
                         width="stretch", icon=":material/query_stats:"):
        st.session_state.page = "stats"
        st.rerun()
    if st.sidebar.button("Выйти", type="primary", width="stretch", icon=":material/close:"):
        st.session_state.clear()
        st.rerun()

# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def render_error_page():
    st.markdown("<h1 style='text-align: center;'>🚨 Системный сбой</h1>", unsafe_allow_html=True)
    st.divider()
    st.error(f"""
    **Обнаружена критическая ошибка конфигурации среды.**
    
    Приложению не удалось получить доступ к необходимым ресурсам. Это может быть связано с отсутствием важных папок или повреждением структуры данных.
    """)
    with st.container(border=True):
        st.markdown("""
        ### 🛠 Что делать?
        1. **Проверьте файлы:** Убедитесь, что папка `/data` существует в корневом каталоге проекта.
        2. **Перезапустите сервер:** Попробуйте остановить Streamlit (Ctrl+C в терминале) и запустить его снова.
        3. **Свяжитесь с разработчиком:** Если вы обычный пользователь, сообщите разработчику код ошибки выше.
        """)
    if st.button("Попробовать снова", icon=":material/refresh:", type="primary"):
        st.session_state.clear()
        st.rerun()
    st.info("Работа симулятора приостановлена для предотвращения повреждения базы данных пациентов.", icon=":material/lock:")
    st.stop()

def render_menu_page():
    st.title(":material/medical_services: Терапевтический симулятор")
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

    st.divider()
    cases_path = st.session_state.path.get("cases")
    cases_count = len(list(cases_path.glob("case*.json"))) if cases_path else 0
    stats = st.session_state.get("stats", {})
    completed = len(stats)
    avg_score = (
        round(sum(s["score"] for s in stats.values()) / completed)
        if completed > 0 else "—"
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Доступно кейсов", value=cases_count)
    with col2:
        st.metric(label="Завершено", value=completed)
    with col3:
        st.metric(label="Средний балл", value=avg_score)

def render_home_page():
    st.title("💼 Мой кабинет")
    if st.session_state.in_work:
        st.info("У вас есть незавершённый приём. Перейдите в **Приёмную** или завершите работу с пациентом.")
    st.markdown("### Выберите клинический случай")
    cases = load_cases()
    stats = st.session_state.get("stats", {})
    for id, case in cases.items():
        col1, col2 = st.columns([9, 1])
        full_name = f"{case['last_name']} {case['first_name'][0]}. {case["patronymic"][0]}."
        with col1:
            if st.session_state.in_work:
                if st.session_state.work_id == id:
                    if st.button(
                        f"{id:<3} | {full_name:^50} | {(str(case['age'])+" лет"):^30} | {"▶   Продолжить":^30}".replace(" ", "\u00A0"),
                        type="primary", width="content"):
                        st.session_state.page = "work"
                        st.rerun()
                else:
                    st.button(
                    f"{id:<3} | {full_name:^50} | {(str(case['age'])+" лет"):^30} | {"🔒   Недоступно":^30}".replace(" ", "\u00A0"),
                    key=f"case_btn_{id}",
                    width="content", 
                    disabled=True)
            else:
                btn_stat = lambda finish: "🔄   Еще раз" if finish else "📋   Начать"
                if st.button(
                    f"{id:<3} | {full_name:^50} | {(str(case['age'])+" лет"):^30} | {btn_stat(id in stats):^30}".replace(" ", "\u00A0"),
                    key=f"case_btn_{id}",
                    width="content"):
                    st.session_state.in_work = True
                    st.session_state.work_id = id
                    st.session_state.page = "work"
                    st.rerun()
                
        with col2:
            if id in stats:
                st.markdown(f"**{stats[id]['score']}%**")
            else:
                st.markdown("—")

def render_work_page():
    if st.session_state.work_id is None:
        st.session_state.page = "home"
        st.session_state.in_work = False
        st.rerun()
        return
    case = load_case(st.session_state.path["cases"] / f"case_{st.session_state.work_id}.json")
    if case is None:
        st.error("Не удалось загрузить данные пациента.")
        return
    
    
    
    st.title(f"🩺 Ваш приемный кабинет")
    ava_path = str(st.session_state.path["avatars"] / case["img"])
    col1, _, col2 = st.columns([20, 1, 29])
    with col1:
        st.image(ava_path, use_container_width=True)
    with col2:
        st.markdown(f"""
            ---
            ##### **ФИО:** {case['last_name']} {case['first_name']} {case['patronymic']}
            ##### **Возраст:** {case['age']}
            ##### **Пол:** {case['sex']}
            ##### **Жалобы:** *{case['history']}*
            ---
        """)
    with st.container(border=True):
        if st.session_state.n_change == True:
            if "dialog" not in st.session_state:
                st.session_state.dialog = f"**{case['first_name']}:** {case["questions"][st.session_state.n]["a"]}"
            else:
                st.session_state.dialog += f"\n\n**Вы:** {case["questions"][st.session_state.n]["q"]}   \n**{case['first_name']}:** {case["questions"][st.session_state.n]["a"]}"
            st.session_state.n_change = False
        st.markdown(st.session_state.dialog)
    _, col1, _ = st.columns([1, 5, 1])
    with col1:
        indexed_questions = list(enumerate(case["questions"]))
        filtered = [
            item for item in indexed_questions 
            if item[0] not in st.session_state.excluded_q and item[1].get('weight', 0) >= 0
        ]
        top_qst = get_top_questions(filtered)
        for q_id, q_item in top_qst.items():
            if st.button(f"{q_item['q']}", use_container_width=True):
                st.session_state.n = q_id
                st.session_state.n_change = True
                st.session_state.excluded_q.append(q_id)
                #st.session_state.weight_stat
                st.rerun()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Завершить работу (прогресс будет удален)", type="primary"):
            st.session_state.excluded_q = []
            st.session_state.n_change = True
            st.session_state.n = 0
            del st.session_state["dialog"]
            st.session_state.in_work = False
            st.session_state.page = "home"
            st.rerun()
    with col2:
        if st.button("Закончить (сохранить прогресс)"):
            st.session_state[f"stat_c{st.session_state.work_id}"]
            st.session_state.excluded_q = []
            st.session_state.n_change = True
            st.session_state.n = 0
            del st.session_state["dialog"]
            st.session_state.in_work = False
            st.session_state.page = "stats"
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

# Запуск программы
if __name__ == "__main__":
    main()