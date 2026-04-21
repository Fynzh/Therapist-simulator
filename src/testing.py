import streamlit as st
import inspect

def generate_st_help():
    with open("streamlit_help.txt", "w", encoding="utf-8") as f:
        # Проходим по всем элементам в модуле streamlit
        for name, obj in inspect.getmembers(st):
            # Нам нужны только функции и те, что не начинаются с подчёркивания
            if not name.startswith("_") and (inspect.isfunction(obj) or inspect.isbuiltin(obj)):
                f.write(f"--- COMMAND: st.{name} ---\n")
                f.write(str(inspect.getdoc(obj)))
                f.write("\n\n" + "="*50 + "\n\n")

if __name__ == "__main__":
    generate_st_help()
    print("Готово! Файл streamlit_help.txt создан.")