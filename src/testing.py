import streamlit as st
import random

def _smart_random(min_val, max_val):
    def get_precision(val):
        s = str(val)
        return len(s.split(".")[1]) if "." in s else 0
    precision = max(get_precision(min_val), get_precision(max_val))
    res = random.uniform(float(min_val), float(max_val))
    return round(res, precision) if precision > 0 else int(round(res))

def main():
    #for i in range(10):
    #    value = _smart_random(4.33, 9.2)
    #    st.info(value)
    data = [
        {"Имя": "Алексей", "Роль": "4.33"},
        {"Имя": "Мария", "Роль": "4.3"}
    ]
    st.table(data)

if __name__ is "__main__":
    main()