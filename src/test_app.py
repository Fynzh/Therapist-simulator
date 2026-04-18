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

# --- ГЛАВНАЯ ФУНКЦИЯ ---
def main():
    st.set_page_config(page_title="Симулятор терапевта", layout="wide")
    
    data_path = get_paths()
    
    # 1. Sidebar - Загрузка списка файлов
    st.sidebar.title("🩺 Управление")
    
    if not data_path.exists():
        st.error(f"❌ Критическая ошибка: Папка {data_path} не найдена!")
        return # Останавливаем выполнение

    files = [f.name for f in data_path.glob("*.json")]
    
    if not files:
        st.warning(f"⚠️ В папке {data_path} нет JSON-файлов.")
        return

    selected_file = st.sidebar.selectbox("Выберите пациента", files)
    
    # 2. Основной экран
    if selected_file:
        case_data = load_case(data_path / selected_file)
        
        if case_data:
            render_patient_screen(case_data)
    else:
        st.info("⬅️ Выберите пациента в боковом меню, чтобы начать.")

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