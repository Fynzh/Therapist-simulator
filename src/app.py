import streamlit as st
import json
from pathlib import Path

# --- КОНФИГУРАЦИЯ ---
def get_paths():
    """Определяет пути к данным независимо от способа запуска."""
    current_dir = Path(__file__).resolve().parent
    # Если мы в /src, корень на уровень выше, если нет — корень здесь
    base_dir = current_dir.parent if current_dir.name == "src" else current_dir
    return base_dir / "data" / "cases"

def load_case(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Ошибка чтения файла: {e}")
        return None

def sidebar_render():
    if st.session_state.page == "home":
        if st.sidebar.button("Главная", type="secondary", width="stretch"):
            st.session_state.page = "home"
            st.rerun()
    else:
        if st.sidebar.button("Главная", type="tertiary", width="stretch"):
            st.session_state.page = "home"
            st.rerun()
    if st.session_state.page == "settings":
        if st.sidebar.button("Настройки", type="secondary", width="stretch"):
            st.session_state.page = "settings"
            st.rerun()
    else:
        if st.sidebar.button("Настройки", type="tertiary", width="stretch"):
            st.session_state.page = "settings"
            st.rerun()
    if st.session_state.page == "stats":
        if st.sidebar.button("Статистика", type="secondary", width="stretch"):
            st.session_state.page = "stats"
            st.rerun()
    else:
        if st.sidebar.button("Статистика", type="tertiary", width="stretch"):
            st.session_state.page = "stats"
            st.rerun()
    if st.sidebar.button("Выйти", type="primary", width="stretch"):
        st.info("Здесь будет логика выхода (очистка сессии)")
# --- ГЛАВНАЯ ФУНКЦИЯ ---
def main():
    if "page" not in st.session_state:
        st.session_state.page = "menu"
    
    if st.session_state.page == "menu":
        render_menu_page()
    elif st.session_state.page == "home":
        render_home_page()
    elif st.session_state.page == "settings":
        render_settings_page()
    elif st.session_state.page == "stats":
        render_stats_page()
    
    sidebar_render()
    # 1. Навигация в Sidebar
    
    
# Функции-заглушки для твоих разделов
def render_menu_page():
    st.title("Главное меню")

def render_home_page():
    st.title("🏠 Главная страница")
    # Твой текущий код с выбором пациента пойдет сюда

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