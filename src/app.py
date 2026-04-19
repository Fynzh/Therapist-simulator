import streamlit as st
import json
from pathlib import Path

try:
    import pandas as pd
    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False


def anti_none():
    defaults = {
        "in_work": False,
        "page": "menu",
        "n": 0,
        "n_change": True,
        "excluded_q": [],
        "work_id": None,
        "stage": "questions",   # questions → exams → diagnosis
        "ordered_exams": [],
        "user_diagnosis": "",
        "stats": {},
        "last_stat_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_work_state():
    st.session_state.excluded_q = []
    st.session_state.n = 0
    st.session_state.n_change = True
    st.session_state.stage = "questions"
    st.session_state.ordered_exams = []
    st.session_state.user_diagnosis = ""
    st.session_state.in_work = False
    st.session_state.work_id = None
    if "dialog" in st.session_state:
        del st.session_state["dialog"]


def init_paths() -> bool:
    current_dir = Path(__file__).resolve().parent
    base_dir = current_dir.parent if current_dir.name == "src" else current_dir
    data_dir = base_dir / "data"

    required_paths = {
        "data": data_dir,
        "cases": data_dir / "cases",
        "avatars": data_dir / "avatars",
        "users": data_dir / "users",
    }

    if "path" not in st.session_state:
        st.session_state.path = {}

    all_clear = True
    for key, path_obj in required_paths.items():
        if not path_obj.exists():
            st.error(f'❌ Критическая ошибка: Папка не найдена: "{path_obj}"')
            all_clear = False
        else:
            st.session_state.path[key] = path_obj

    # media — опциональная папка для файлов анализов
    media_path = data_dir / "media"
    st.session_state.path["media"] = media_path if media_path.exists() else None

    return all_clear


def load_cases() -> dict:
    cases_dict = {}
    cases_path = st.session_state.path.get("cases")
    if not cases_path or not cases_path.is_dir():
        return cases_dict
    for file_path in sorted(cases_path.glob("case*.json")):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            case_id = data.get("id")
            if case_id is not None:
                cases_dict[case_id] = {
                    "last_name": data.get("last_name"),
                    "first_name": data.get("first_name"),
                    "patronymic": data.get("patronymic"),
                    "age": data.get("age"),
                    "sex": data.get("sex"),
                    "answer": data.get("answer"),
                }
        except (json.JSONDecodeError, OSError) as e:
            print(f"Ошибка при чтении {file_path.name}: {e}")
    return cases_dict


def load_case(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Ошибка чтения файла: {e}")
        return None


def get_top_questions(questions, limit=3):
    sorted_questions = sorted(questions, key=lambda x: x[1].get("weight", 0), reverse=True)
    return {
        orig_id: {"q": item["q"], "a": item["a"], "weight": item["weight"]}
        for orig_id, item in sorted_questions[:limit]
    }


def calculate_score(case, asked_ids):
    """Балл = сумма весов заданных вопросов / сумма всех возможных весов (weight > 0)."""
    total = sum(q["weight"] for q in case["questions"] if q.get("weight", 0) > 0)
    asked = sum(
        case["questions"][q_id]["weight"]
        for q_id in asked_ids
        if case["questions"][q_id].get("weight", 0) > 0
    )
    if total == 0:
        return 0
    return round((asked / total) * 100)


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
    st.error("""
    **Обнаружена критическая ошибка конфигурации среды.**

    Приложению не удалось получить доступ к необходимым ресурсам.
    """)
    with st.container(border=True):
        st.markdown("""
        ### 🛠 Что делать?
        1. **Проверьте файлы:** Убедитесь, что папка `/data` существует в корне проекта.
        2. **Перезапустите сервер:** Остановите Streamlit (Ctrl+C) и запустите снова.
        3. **Свяжитесь с разработчиком:** Сообщите об ошибке.
        """)
    if st.button("Попробовать снова", icon=":material/refresh:", type="primary"):
        st.session_state.clear()
        st.rerun()
    st.info("Работа симулятора приостановлена.", icon=":material/lock:")
    st.stop()


def render_menu_page():
    st.title(":material/medical_services: Терапевтический симулятор")
    st.markdown("""
    ### Добро пожаловать в систему интерактивного обучения!

    Этот симулятор разработан для отработки навыков **клинического мышления** терапевта:
    сбора анамнеза, назначения обследований и постановки диагноза.

    ---

    ### 🎯 Ваша задача:
    1. **Собрать анамнез** — задавайте вопросы пациенту.
    2. **Назначить обследования** — выберите нужные анализы и исследования.
    3. **Поставить диагноз** — на основе собранных данных сформулируйте заключение.

    > **Помните:** Эффективность оценивается по ценности заданных вопросов.
    > Избегайте лишних вопросов и исследований.
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
        st.metric("Доступно кейсов", cases_count)
    with col2:
        st.metric("Завершено", completed)
    with col3:
        st.metric("Средний балл", avg_score)


def render_home_page():
    st.title("💼 Мой кабинет")
    if st.session_state.in_work:
        st.info("У вас есть незавершённый приём. Перейдите в **Приёмную** или завершите работу с пациентом.")
    st.markdown("### Выберите клинический случай")
    cases = load_cases()
    stats = st.session_state.get("stats", {})

    for case_id, case in cases.items():
        col_btn, col_score = st.columns([9, 1])
        full_name = f"{case['last_name']} {case['first_name'][0]}. {case['patronymic'][0]}."
        label = (
            f"{case_id:<3} | {full_name:^50} | {str(case['age']) + ' лет':^15}"
        ).replace(" ", "\u00A0")

        with col_btn:
            if st.session_state.in_work:
                if st.session_state.work_id == case_id:
                    if st.button(f"▶ Продолжить: {full_name}", key=f"case_btn_{case_id}",
                                 type="primary", width="content"):
                        st.session_state.page = "work"
                        st.rerun()
                else:
                    st.button(label, key=f"case_btn_{case_id}", width="content", disabled=True)
            else:
                if st.button(label, key=f"case_btn_{case_id}", width="content"):
                    reset_work_state()
                    st.session_state.in_work = True
                    st.session_state.work_id = case_id
                    st.session_state.page = "work"
                    st.rerun()

        with col_score:
            if case_id in stats:
                st.markdown(f"**{stats[case_id]['score']}%**")
            else:
                st.markdown("—")


# ---------------------------------------------------------------------------
# Work page — 3 stages
# ---------------------------------------------------------------------------

def render_work_page():
    if st.session_state.work_id is None:
        st.session_state.page = "home"
        st.rerun()
        return

    case = load_case(
        st.session_state.path["cases"] / f"case_{st.session_state.work_id}.json"
    )
    if case is None:
        st.error("Не удалось загрузить данные пациента.")
        return

    stage = st.session_state.stage
    if stage == "questions":
        _render_questions_stage(case)
    elif stage == "exams":
        _render_exams_stage(case)
    elif stage == "diagnosis":
        _render_diagnosis_stage(case)


def _render_patient_card(case):
    ava_path = str(st.session_state.path["avatars"] / case["img"])
    col_img, _, col_info = st.columns([4, 1, 8])
    with col_img:
        st.image(ava_path, use_container_width=True)
    with col_info:
        st.markdown(f"""
---
**ФИО:** {case['last_name']} {case['first_name']} {case['patronymic']}
**Возраст:** {case['age']} лет
**Пол:** {case['sex']}
**Жалобы:** *{case['history']}*

---
""")


def _render_questions_stage(case):
    st.title("🩺 Опрос пациента")
    _render_patient_card(case)

    # Диалог -----------------------------------------------------------------
    with st.container(border=True):
        if st.session_state.n_change:
            n = st.session_state.n
            if "dialog" not in st.session_state:
                # Инициализация: показываем приветствие пациента (вопрос с индексом 0)
                st.session_state.dialog = (
                    f"**{case['first_name']}:** {case['questions'][0]['a']}"
                )
            else:
                q = case["questions"][n]
                st.session_state.dialog += (
                    f"\n\n**Вы:** {q['q']}  \n**{case['first_name']}:** {q['a']}"
                )
            st.session_state.n_change = False
        st.markdown(st.session_state.dialog)

    # Доступные вопросы (исключаем приветствие idx=0, уже заданные и weight≤0)
    indexed_questions = list(enumerate(case["questions"]))
    filtered = [
        item for item in indexed_questions
        if item[0] != 0
        and item[0] not in st.session_state.excluded_q
        and item[1].get("weight", 0) > 0
    ]
    top_qst = get_top_questions(filtered)

    _, col_q, _ = st.columns([1, 5, 1])
    with col_q:
        if top_qst:
            st.markdown("**Выберите вопрос:**")
            for q_id, q_item in top_qst.items():
                if st.button(q_item["q"], use_container_width=True, key=f"q_{q_id}"):
                    st.session_state.n = q_id
                    st.session_state.n_change = True
                    st.session_state.excluded_q.append(q_id)
                    st.rerun()
        else:
            st.info("Все доступные вопросы заданы.")

    st.divider()
    col_abort, col_next = st.columns(2)
    with col_abort:
        if st.button("❌ Завершить без сохранения", type="secondary"):
            reset_work_state()
            st.session_state.page = "home"
            st.rerun()
    with col_next:
        if st.button("🔬 Перейти к назначению анализов →", type="primary"):
            st.session_state.stage = "exams"
            st.rerun()


def _render_exams_stage(case):
    st.title("🔬 Назначение обследований")
    st.markdown(
        f"**Пациент:** {case['last_name']} {case['first_name']} {case['patronymic']}, "
        f"{case['age']} лет"
    )
    st.markdown("Отметьте обследования, которые хотите назначить:")
    st.divider()

    exams = case.get("exams", [])
    if not exams:
        st.info("Для данного пациента обследований не предусмотрено.")
    else:
        ordered = list(st.session_state.ordered_exams)
        for i, exam in enumerate(exams):
            checked = exam["name"] in ordered
            if st.checkbox(exam["name"], value=checked, key=f"exam_{i}"):
                if exam["name"] not in ordered:
                    ordered.append(exam["name"])
            else:
                if exam["name"] in ordered:
                    ordered.remove(exam["name"])
        st.session_state.ordered_exams = ordered

    st.divider()
    col_back, _, col_next = st.columns(3)
    with col_back:
        if st.button("← Вернуться к опросу", type="secondary"):
            st.session_state.stage = "questions"
            st.rerun()
    with col_next:
        if st.button("📋 Посмотреть результаты →", type="primary"):
            st.session_state.stage = "diagnosis"
            st.rerun()


def _render_diagnosis_stage(case):
    st.title("📋 Результаты и диагноз")
    st.markdown(
        f"**Пациент:** {case['last_name']} {case['first_name']} {case['patronymic']}, "
        f"{case['age']} лет"
    )
    st.divider()

    # Результаты обследований ------------------------------------------------
    ordered_names = st.session_state.ordered_exams
    ordered_exams = [e for e in case.get("exams", []) if e["name"] in ordered_names]

    if not ordered_exams:
        st.warning("Вы не назначили ни одного обследования.")
    else:
        st.markdown("### Результаты назначенных обследований")
        media_path = st.session_state.path.get("media")
        for exam in ordered_exams:
            with st.expander(f"📄 {exam['name']}", expanded=True):
                fpath = (media_path / exam["file_name"]) if media_path else None
                if fpath and fpath.exists():
                    if exam["type"] == "image":
                        st.image(str(fpath))
                    elif exam["type"] == "table" and _HAS_PANDAS:
                        try:
                            df = pd.read_csv(fpath)
                            st.dataframe(df, use_container_width=True)
                        except Exception:
                            st.error("Не удалось загрузить таблицу.")
                    else:
                        st.info("Формат файла не поддерживается.")
                else:
                    st.info("Результаты исследования ещё не готовы.")

    st.divider()

    # Ввод диагноза ----------------------------------------------------------
    st.markdown("### Ваш диагноз")
    diagnosis = st.text_input(
        "Введите предварительный диагноз:",
        value=st.session_state.user_diagnosis,
        placeholder="Например: Острый аппендицит",
    )
    st.session_state.user_diagnosis = diagnosis

    col_back, _, col_finish = st.columns(3)
    with col_back:
        if st.button("← Вернуться к анализам", type="secondary"):
            st.session_state.stage = "exams"
            st.rerun()
    with col_finish:
        if st.button(
            "✅ Завершить и получить оценку",
            type="primary",
            disabled=not diagnosis.strip(),
        ):
            _save_stat(case)
            saved_id = st.session_state.work_id
            reset_work_state()
            st.session_state.last_stat_id = saved_id
            st.session_state.page = "stats"
            st.rerun()


def _save_stat(case):
    score = calculate_score(case, st.session_state.excluded_q)
    correct = case["answer"]
    user_diag = st.session_state.user_diagnosis.strip()
    if "stats" not in st.session_state:
        st.session_state.stats = {}
    st.session_state.stats[st.session_state.work_id] = {
        "score": score,
        "asked_ids": list(st.session_state.excluded_q),
        "ordered_exams": list(st.session_state.ordered_exams),
        "user_diagnosis": user_diag,
        "correct_diagnosis": correct,
        "is_correct": user_diag.lower() == correct.lower(),
        "case_name": f"{case['last_name']} {case['first_name']} {case['patronymic']}",
    }


# ---------------------------------------------------------------------------

def render_settings_page():
    st.title("⚙️ Настройки")
    st.write("Настройки интерфейса (в разработке).")


def render_stats_page():
    st.title("📊 Статистика")
    stats = st.session_state.get("stats", {})

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


if __name__ == "__main__":
    main()
