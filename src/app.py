import streamlit as st
import json
import time
import random
import extra_streamlit_components as stx
from typing import Literal
from pathlib import Path

def init_manager():
    return stx.CookieManager()

cm = init_manager()

def anti_none():
    defaults = {
        "in_work": False,
        "n": 0,
        "n_change": True,
        "excluded_q": [0],
        "work_id": None,
        "path" : {},
        "ordered_exams": [],
        "user_diagnosis": "",
        "stats": {},
        "auth": False,
        "user_f": None,
        "anim_dia": False,
        "top_qst": {},
        "cookie_save": False,
        "cookie_delete": False,
        "user_logout": False,
        "exams_stage": "appointment",
        "show_keys": {},
        "settings": {
            "img_info" : True,
            "norms": True
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def init_paths(current_dir = Path(__file__).resolve().parent) -> bool:
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

def sync_settings():
    for k, _ in st.session_state.settings.items():
        st.session_state.settings[k] = st.session_state[f"temp_{k}"]

def _logout():
    st.session_state.auth = False
    st.session_state.user_f = None
    st.session_state.page = "auth"
    st.rerun

def _login_id(id):
    users_dir = st.session_state.path["users"]
    for user_file in users_dir.glob("*.json"):
        try:
            data = json.loads(user_file.read_text(encoding="utf-8"))
            if data.get("id") == id:
                st.session_state.user_f = st.session_state.path["users"] / user_file.name
                if "page" not in st.session_state:
                    st.session_state.page = "menu"
                if st.session_state.auth == False or "auth" not in st.session_state:
                    st.session_state.auth = True
                _load_progress()
                return True
        except (json.JSONDecodeError, IOError):
            return False

def _login(username) -> bool:
    # 1. Определяем путь к папке как объект Path
    users_dir = st.session_state.path["users"]
    
    # 2. Поиск существующего пользователя
    # .glob('*.json') находит все файлы с расширением .json
    for user_file in users_dir.glob("*.json"):
        try:
            # .read_text() сам открывает и закрывает файл
            data = json.loads(user_file.read_text(encoding="utf-8"))
            if data.get("username") == username:
                # .name возвращает только имя файла (напр. "user_001.json")
                st.session_state.user_f = st.session_state.path["users"] / user_file.name
                if st.session_state.page == "auth" or "page" not in st.session_state:
                    st.session_state.page = "menu"
                _load_progress()
                return True
        except (json.JSONDecodeError, IOError):
            return False

    # 3. Создание нового пользователя, если не нашли
    user_files = list(users_dir.glob("user_*.json"))
    
    if not user_files:
        new_id = 1
    else:
        # Извлекаем числа из имен файлов
        # f.stem — это имя файла без расширения ("user_001")
        existing_ids = []
        for f in user_files:
            try:
                num = int(f.stem.split('_')[1])
                existing_ids.append(num)
            except (IndexError, ValueError):
                return False
        new_id = max(existing_ids) + 1 if existing_ids else len(user_files) + 1

    # Формируем путь к новому файлу
    new_file_name = f"user_{new_id}.json"
    new_path = users_dir / new_file_name
    
    new_user_data = {
        "id": new_id,
        "username": username,
        "stats": {},
        "created_at": "2026-04-19"
    }
    
    # Записываем данные в файл
    new_path.write_text(
        json.dumps(new_user_data, ensure_ascii=False, indent=4), 
        encoding="utf-8"
    )
    
    st.session_state.user_f = st.session_state.path["users"] / new_file_name
    st.session_state.page = "menu"
    return True

def load_stats():
    filepath = st.session_state.user_f
    if filepath and filepath.exists():
        try:
            user_data = json.loads(filepath.read_text(encoding="utf-8"))
            raw_stats = user_data.get("stats", {})
            return {int(k): v for k, v in raw_stats.items() if k.isdigit()}
        except (json.JSONDecodeError, IOError):
            return {}
    else:
        return {}

def load_cases() -> dict:
    cases_dict = {}
    cases_path = st.session_state.path["cases"]
    if not cases_path.is_dir():
        st.error(f"Ошибка: Путь {cases_path} не найден или не является папкой.")
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
                    "correct_diagnosis": data.get("correct_diagnosis")
                }
        except (json.JSONDecodeError, OSError) as e:
            st.error(f"Ошибка при чтении файла {file_path.name}: {e}")
    return cases_dict

def load_case(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Ошибка чтения файла: {e}")
        return None

def load_exams(case):
    if "loaded_exams" in st.session_state:
        return
    st.session_state.loaded_exams = []
    exams_list = []
    exams_path = st.session_state.path["data"] / "exams_standart.json"
    if not exams_path.is_file():
        st.error(f"Ошибка: Файл {exams_path} не найден.")
        return exams_list
    try:
        exams_dict = json.loads(exams_path.read_text(encoding='utf-8'))
        exams_list = exams_dict["exams"]
    except (json.JSONDecodeError, OSError) as e:
        st.error(f"Ошибка при чтении файла {exams_path.name}: {e}")
    
    case_exams_map = {ex["name"]: ex for ex in case["exams"]}
    
    for exam_norm in exams_list:
        exam_name = exam_norm["name"]
        if exam_name in case_exams_map:
            load_exam = case_exams_map[exam_name].copy()
            if load_exam.get("type") == "table":
                load_exam["info"] = _table_norm_generate(exam_norm["info"], case_exams_map[exam_name]["info"])
        else:
            load_exam = exam_norm.copy()
            if exam_norm.get("type") == "table":
                load_exam["info"] = _table_processing(exam_norm["info"])
        st.session_state.loaded_exams.append(load_exam)
    return True

def _table_norm_generate(norm_t, case_t):
    processed_table = []
    case_t_map = {ex["Параметр"]: ex for ex in case_t}
    for arg in norm_t:
        if arg["Параметр"] in case_t_map:
            if "text" in arg:
                processed_table.append(case_t_map[arg["Параметр"]])
            elif "min" in arg and "max" in arg:
                mi, ma = arg["min"], arg["max"]
                processed_arg = {}
                for key, value in case_t_map[arg["Параметр"]].items():
                    processed_arg[key] = str(value)
                processed_arg["Норма"] = f"{str(mi)} - {str(ma)}"
                processed_table.append(processed_arg)
    return processed_table

def _table_processing(raw_table: list) -> list:
    processed_table = []
    for arg in raw_table:
        if "text" in arg:
            processed_table.append(arg)
        elif "min" in arg and "max" in arg:
            mi, ma = arg["min"], arg["max"]
            random_val = _smart_random(min_val=mi, max_val=ma)
            processed_arg = {}
            for key, value in arg.items():
                if key == "min" or key == "max":
                    processed_arg["Значение"] = str(random_val)
                else:
                    processed_arg[key] = value
            processed_arg["Норма"] = f"{str(mi)} - {str(ma)}"
            processed_table.append(processed_arg)
    return processed_table

def _smart_random(min_val, max_val):
    def get_precision(val):
        s = str(val)
        return len(s.split(".")[1]) if "." in s else 0
    precision = max(get_precision(min_val), get_precision(max_val))
    res = random.uniform(float(min_val), float(max_val))
    return round(res, precision) if precision > 0 else int(round(res))

def reset_work_state():
    for_reset = {
        "excluded_q": [0],
        "n": 0,
        "n_change": True,
        "ordered_exams": [],
        "user_diagnosis": "",
        "in_work": False,
        "work_id": None,
        "show_keys": {},
        "exams_stage": "appointment"
    }
    for_del = [
        "dialog",
        "loaded_exams"
    ]
    for k, v in for_reset.items():
        if k in st.session_state:
            st.session_state[k] = v
    for v in for_del:
        if v in st.session_state:
            del st.session_state[v]
    _save_progress()

def _save_stat(case):
    exc_q = [x for x in st.session_state.excluded_q if x != 0]
    score = calculate_score(case, exc_q)
    exams_score = calculate_score(case, used_ids=st.session_state.ordered_exams, atribute="exams")
    correct = case["correct_diagnosis"]
    user_diag = st.session_state.user_diagnosis.strip()
    if "current_stats" not in st.session_state:
        st.session_state.current_stats = {}
    st.session_state.current_stats[st.session_state.work_id] = {
        "score": score,
        "asked_ids": list(st.session_state.excluded_q),
        "ordered_exams": list(st.session_state.ordered_exams),
        "exams_score": exams_score,
        "user_diagnosis": user_diag,
        "correct_diagnosis": correct,
        "is_correct": user_diag.lower() == correct.lower(),
        "case_name": f"{case['last_name']} {case['first_name']} {case['patronymic']}",
    }

def _save_progress():
    progress_info = [
        "in_work", "page", "n", "n_change", "excluded_q",
        "work_id", "ordered_exams", "user_diagnosis",
        "stats", "anim_dia", "top_qst", "dialog", "loaded_exams", 
        "show_keys", "settings"
        ]
    progress = {}
    for inf in progress_info:
        if inf not in progress and inf in st.session_state:
            progress[inf] = st.session_state[inf]
    _export(progress = progress)

def _load_progress():
    loads = _import("progress")
    try:
        if loads:
            for key, value in loads.items():
                if key not in st.session_state or not st.session_state[key] == value:
                    conv_val = convert_keys_to_int(value)
                    st.session_state[key] = conv_val
            return
    except:
        st.error("Ошибка загрузки предыдущей сессии")

def convert_keys_to_int(data):
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if isinstance(k, str) and k.isdigit():
                new_key = int(k)
            else:
                new_key = k
            
            new_dict[new_key] = convert_keys_to_int(v)
        return new_dict
    elif isinstance(data, list):
        return [convert_keys_to_int(item) for item in data]
    else:
        return data

def _export(**info) -> bool:
    filepath = st.session_state.user_f
    if not filepath or not filepath.exists():
        st.error("Ошибка записи данных, пользователь не авторизован")
        _logout()
        return False
    
    try:
        user_data = json.loads(filepath.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        st.error("Ошибка записи данных, пожалуйста, авторизуйтесь повторно.")
        _logout()
        return False

    # 3. Записываем текущую статистику под ключом айди кейса
    for item, value in info.items():
        if item not in user_data:
            user_data[item] = {}
        user_data[item] = value

    # 4. Сохраняем файл обратно
    filepath.write_text(
        json.dumps(user_data, ensure_ascii=False, indent=4), 
        encoding="utf-8"
    )
    return True

def _import(data):
    filepath = st.session_state.user_f
    if filepath and filepath.exists():
        try:
            user_data = json.loads(filepath.read_text(encoding="utf-8"))
            return user_data.get(data)
        except (json.JSONDecodeError, IOError):
            return None
    else:
        return None

def get_top_questions(questions, limit=5):
    # Превращаем в список кортежей (id, data) для удобства
    items = questions
    
    # 1. Сортируем по категориям или весу
    critical = [it for it in items if it[1].get('weight', 0) >= 8]
    medium = [it for it in items if 4 <= it[1].get('weight', 0) < 8]
    low_or_error = [it for it in items if it[1].get('weight', 0) < 4]
    
    # 2. Формируем выборку
    selected = []
    
    # Берем 2 самых важных (чтобы не пропустить базу)
    selected.extend(random.sample(critical, min(2, len(critical))))
    
    # Берем 2 средних (дифдиагноз)
    selected.extend(random.sample(medium, min(2, len(medium))))
    
    # Добираем остальное до лимита из "шума" или оставшихся
    remaining = [it for it in items if it not in selected]
    needed = limit - len(selected)
    if needed > 0:
        selected.extend(random.sample(remaining, min(needed, len(remaining))))
    
    # Перемешиваем, чтобы важные вопросы не всегда были вверху списка
    random.shuffle(selected)
    
    return {
        orig_id: {
            "q": item["q"],
            "a": item["a"],
            "weight": item["weight"]
        }
        for orig_id, item in selected
    }

def calculate_score(case, used_ids, atribute: Literal["questions", "exams"] = "questions"):
    if not used_ids:
        return 0
    total = len(used_ids) * 10
    if total == 0:
        return 0
    if atribute == "questions":
        user_weight = sum(case[atribute][int(q_id)]['weight'] for q_id in used_ids)
    elif atribute == "exams":
        user_weight = sum(exam["weight"] for exam in used_ids)
    score = round((user_weight / total) * 100)
    return min(100, score)

def show_info(info: str, key, button_text: str = "Закрыть"):
    if key:
        show_key = key
    else:
        show_key = f"has_seen_{info[:15]}"
    
    if show_key in st.session_state.show_keys and not st.session_state.show_keys[show_key]:
        return

    # Инициализируем состояние, если это первый запуск
    if show_key not in st.session_state.show_keys:
        st.session_state.show_keys[show_key] = True

    # Отрисовываем контейнер
    placeholder = st.empty()
    with placeholder.container(border=True):
        st.info(info)
        # Используем on_click для мгновенного обновления состояния до рендеринга
        st.button(
            button_text, 
            key=f"btn_{show_key}", # Уникальный ключ для самой кнопки
            on_click=lambda: st.session_state.show_keys.update({show_key: False})
        )

def sidebar_render():
    with st.sidebar:
        st.caption(f"Вы вошли как: {_import("username")}")
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
    if st.sidebar.button("Сохранить и выйти", type="primary", width="stretch", icon=":material/close:"):
        _save_progress()
        st.session_state.clear()
        st.session_state.cookie_delete = True
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

def render_auth_page():
    st.title(":material/medical_services: Терапевтический симулятор")
    st.subheader("Добро пожаловать в систему симуляции клинических случаев")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        Этот симулятор разработан для отработки навыков:
        * **Сбора анамнеза** (выбор правильных вопросов пациенту)
        * **Физикального осмотра** и интерпретации анализов
        * **Постановки диагноза** на основе клинических рекомендаций
        
        *Ваша задача: макимально точно определить патологию, минимизировав лишние назначения.*
        """)
    
    with col2:
        # Можно добавить иконку или декоративный элемент
        st.info("📊 Статистика ваших приемов будет сохраняться в личный профиль.")

    st.divider()

    # 3. Форма авторизации
    st.write("### Вход в систему")
    
    # Создаем контейнер, чтобы ограничить ширину поля ввода
    with st.container():
        st.text_input(
            "Введите ваше имя или ID врача", 
            placeholder="Логин",
            help="Это имя будет использоваться в отчетах и результатах кейсов",
            key="user_name",
            on_change=_button_auth
        )
        st.button("Войти в кабинет", type="primary", width="stretch", on_click=_button_auth)
    st.stop()

def _button_auth():
    user_name = st.session_state.user_name
    if user_name.strip():
        if _login(user_name):
            st.session_state.cookie_save = True
            st.session_state.auth = True
        else:
            st.error("Ошибка авторизации, попробуйте снова.")
    else:
        st.error("Пожалуйста, введите имя, чтобы продолжить.")

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
    stats = load_stats()
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
    st.title(f"🩺 Ваш приемный кабинет")
    if st.session_state.work_id is None:
        st.session_state.page = "home"
        st.session_state.in_work = False
        st.rerun()
        return
    case = load_case(st.session_state.path["cases"] / f"case_{st.session_state.work_id}.json")
    if case is None:
        st.error("Не удалось загрузить данные пациента.")
        return
    load_exams(case)
    st.markdown("""
        <style>
        button[data-baseweb="tab"] {
            flex-grow: 1;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["💬 Опрос", "🔬 Лаборатория", "📋 Заключение"])
    with tab1:
        _render_questions_stage(case)
    with tab2:
        _render_exams_stage(case)
    with tab3:
        _render_diagnosis_stage(case)

def _render_patient_card(case):
    ava_path = str(st.session_state.path["avatars"] / case["img"])
    col1, _, col2 = st.columns([20, 1, 29])
    with col1:
        st.image(ava_path, width="stretch")
    with col2:
        with st.container(border=True, height=250):
            st.markdown(f"""
                ##### **ФИО:** {case['last_name']} {case['first_name']} {case['patronymic']}
                ##### **Возраст:** {case['age']} лет
                ##### **Пол:** {case['sex']}
                **Жалобы:** *{case['history']}*
            """)

def _render_questions_stage(case):
    _render_patient_card(case)
    if "speed" in case:
        speed = case["speed"]
    else:
        speed = 0.03
    
    with st.container(border=True, autoscroll=True, height=300):
        if st.session_state.n_change == True:
            n=st.session_state.n
            q = case["questions"][n]
            if "dialog" not in st.session_state:
                st.session_state.dialog = ""
                header = f"**{case['first_name']}:** "
            else:
                header = f"\n\n**Вы:** {q["q"]}   \n**{case['first_name']}:** "
            
            placeholder = st.empty()
            full_response = ""
            
            st.session_state.anim_dia = True

            for w in q["a"]:
                full_response += w
                placeholder.markdown(st.session_state.dialog + header + full_response)
                time.sleep(speed)
            
            st.session_state.dialog += header + full_response
            st.session_state.anim_dia = False
            st.session_state.n_change = False
            placeholder.empty()
            
            indexed_questions = list(enumerate(case["questions"]))
            filtered = [
                item for item in indexed_questions 
                if item[0] not in st.session_state.excluded_q
            ]
            st.session_state.top_qst = get_top_questions(filtered)

            st.rerun()
        elif not st.session_state.anim_dia:
            st.markdown(st.session_state.dialog)
    
    if st.session_state.exams_stage == "review":
        st.subheader("Пациент ушел сдавать анализы...")
    else:
        _, col1, _ = st.columns([1, 5, 1])
        with col1:
            if st.session_state.top_qst:
                for q_id, q_item in st.session_state.top_qst.items():
                    if st.button(q_item['q'], width="stretch", key=f"q_{q_id}"):
                        st.session_state.n = q_id
                        st.session_state.n_change = True
                        st.session_state.excluded_q.append(q_id)
                        _save_stat(case)
                        st.rerun()
            else:
                st.info("Все доступные вопросы заданы.")
        show_info("""
            #### Как работает опрос:

            * **Каждый вопрос — это «шаг»:** Чем больше лишних кликов, тем ниже итоговый балл. Это имитация реального приема: нельзя тратить время на пустую болтовню, когда пациенту плохо.
            * **Вес вопроса:**  Ключевые факты дают максимум очков, второстепенные — меньше.
            * **Назначайте анализы после опроса:**  Когда вы назначите пациенту анализы, он уйдет, и вы больше не сможете задать ему вопросы.
            
            ***Подсказка:*** *не перебирай все возможные вопросы, это понизит оценку.*
            """,
            "qst_info", "Понятно")
    
def _render_exams_stage(case):
    st.title("🔬 Лаборатория")
    if st.session_state.exams_stage == "appointment":
        _render_exams_appointment(case)
    elif st.session_state.exams_stage == "review":
        _render_exams_review(case)

def _render_exams_appointment(case):
    st.subheader("Отметьте обследования, которые хотите назначить:")

    with st.container(border=True, height=400):
        exams = st.session_state.loaded_exams
        if not exams:
            st.info("Для данного пациента обследований не предусмотрено.")
        else:
            ordered = list(st.session_state.ordered_exams)
            for i, exam in enumerate(exams):
                checked = exam in ordered
                if st.checkbox(exam["name"], value=checked, key=f"exam_{i}"):
                    if not checked:
                        ordered.append(exam)
                else:
                    if checked:
                        ordered.remove(exam)
            st.session_state.ordered_exams = ordered

    with st.container(horizontal_alignment="right"):
        if st.button("📋 Подтвердить выбор и посмотреть результаты →", type="primary"):
            st.session_state.exams_stage = "review"
            _save_stat(case)
            st.rerun()
    st.divider()
    show_info("""
        #### Как считаются баллы за анализы:

        * **Чем больше вы назначите "бесполезных" анализов - тем больше потратите времени и денег, так что за такое баллы снижаются**
        * **Вес вопроса:**  Ключевые анализы дают максимум, второстепенные — меньше.

        ***Подсказка:*** *не выбирай все возможные анализы, это понизит оценку.*
        """,
        "exams_info", "Понятно")

def _render_exams_review(case):
    st.subheader("Вот результаты назначенных анализов:")
    for exam in st.session_state.ordered_exams:
        with st.expander(exam["name"], ):
            if exam["type"] == "text":
                st.write(exam["info"])
            elif exam["type"] == "table":
                st.table(exam["info"])
            elif exam["type"] == "img":
                file_name = exam.get("file_name")
                file_path = st.session_state.path["media"] / exam["file_name"]
                if file_name and file_path.exists():
                    st.image(file_path)
                else:
                    st.error("Ошибка: Изображение не найдено")
                if exam.get("info") and st.session_state.settings["img_info"]:
                    st.write(exam["info"])

def _render_diagnosis_stage(case):
    
    
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Завершить без сохранения", type="secondary"):
            st.session_state.stats.pop(st.session_state.work_id, None)
            reset_work_state()
            st.session_state.page = "home"
            st.rerun()
    with col2:
        with st.container(horizontal_alignment="right"):
            if st.button("🏁 Закончить прием", type="primary"):
                _save_stat(case)
                if _export(stats=st.session_state.current_stats):
                    reset_work_state()
                    st.session_state.page = "stats"
                    st.rerun()

def render_settings_page():
    st.title("⚙️ Настройки")
    st.write("Настройки интерфейса или сложности.")
    stg_info = {
        "img_info": "Показывать информацию о картинках",
        "norms": "Показывать нормы"
    }
    for stg, v in st.session_state.settings.items():
        st.checkbox(
            label=stg_info[stg], 
            key=f"temp_{stg}", # Временный ключ для связи
            value=st.session_state.settings[stg], # Начальное значение
            on_change=sync_settings # Функция обновления основного словаря
        )
    

def render_stats_page():
    st.title("📊 Статистика")
    stats = load_stats()

    if not stats:
        st.info("Вы ещё не завершили ни одного клинического случая.")
        if st.button("Перейти к кейсам", type="primary"):
            st.session_state.page = "home"
            st.rerun()
        return

    last_id = st.session_state.get("last_stat_id")

    for case_id, s in sorted(stats.items()):
        with st.container(border=True):
            if case_id == last_id:
                st.markdown("### 🆕 Последний результат")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Пациент", s["case_name"])
            with col2:
                st.metric("Балл за опрос", f"{s['score']}%")
            with col3:
                verdict = "✅ Верно" if s["is_correct"] else "❌ Неверно"
                st.metric("Диагноз", verdict)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown(f"**Ваш диагноз:** {s['user_diagnosis']}")
            with col_d2:
                if s["is_correct"]:
                    st.success(f"**Правильный диагноз:** {s['correct_diagnosis']}")
                else:
                    st.error(f"**Правильный диагноз:** {s['correct_diagnosis']}")

            exams_str = ", ".join(s["ordered_exams"]) if s["ordered_exams"] else "не назначены"
            st.markdown(f"**Назначенные исследования:** {exams_str}")

# ---------------------------------------------------------------------------

def main():
    anti_none()
    if not init_paths():
        st.session_state.page = "error"
        render_error_page()
    if st.session_state.cookie_save == True:
        time.sleep(0.5)
        user_id = _import("id")
        cm.set("therapist-simulator-uid", user_id, key="save_uid_action")
        st.session_state.cookie_save = False
        time.sleep(0.5)
        st.rerun()
    if st.session_state.cookie_delete == True:
        user_id = _import("id")
        all_cookies = cm.get_all()
        time.sleep(0.5) # Получаем все куки разом
        if "therapist-simulator-uid" in all_cookies:
            cm.delete("therapist-simulator-uid", key="delete_uid_action")
            time.sleep(0.5)
        st.session_state.user_logout = True
        st.session_state.cookie_delete = False
        st.session_state.auth = False
        if "page" in st.session_state:
            del st.session_state["page"]
        st.rerun()
    if "page" not in st.session_state:
        time.sleep(0.5)
        if st.session_state.user_logout == True:
            st.session_state.page = "auth"
            st.session_state.user_logout = False
            st.rerun()
        elif st.session_state.auth == False:
            user_id = cm.get(cookie="therapist-simulator-uid")
            if user_id:
                if _login_id(user_id):
                    st.rerun()
                else:
                    st.session_state.page = "auth"
                    st.rerun()
            else:
                st.session_state.page = "auth"
                st.rerun()
        else:
            st.session_state.page = "error"
    if st.session_state.page == "error":
        render_error_page()
    elif st.session_state.page == "auth":
        render_auth_page()
    _save_progress()
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