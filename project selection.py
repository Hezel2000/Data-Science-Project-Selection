import streamlit as st
import sqlite3
import pandas as pd

DB = "projects.db"

projects = [
    "Oxygen isotopes in chondrules",
    "Diffusion profiles in garnet",
    "Volcanic ash geochemistry",
    "Machine learning for mineral classification",
]

# --- database setup ---
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    title TEXT UNIQUE,
    claimed_by TEXT
)
""")

for p in projects:
    c.execute(
        "INSERT OR IGNORE INTO projects (title, claimed_by) VALUES (?, NULL)",
        (p,)
    )

conn.commit()

# --- app ---
st.title("Project Suggestions")

student_name = st.text_input("Enter your email")

df = pd.read_sql_query("SELECT * FROM projects", conn)

for _, row in df.iterrows():
    claimed = row["claimed_by"] is not None

    if claimed:
        st.markdown(
            f"""
            <div style="
                background-color:rgba(107,46,46,0.25);
                color:#6B2E2E;
                border:1px solid #6B2E2E;
                padding:12px;
                border-radius:8px;
                margin-bottom:8px;">
                <b>{row['title']}</b><br>
                Claimed by: {row['claimed_by']}
            </div>
            """,
            unsafe_allow_html=True
        )

        if student_name.strip() == row["claimed_by"]:
            if st.button("Give back this project", key=f"return_{row['id']}"):
                c.execute(
                    "UPDATE projects SET claimed_by=NULL WHERE id=? AND claimed_by=?",
                    (row["id"], student_name.strip())
                )
                conn.commit()
                st.rerun()

    else:
        st.markdown(
            f"""
            <div style="
                background-color:rgba(85,107,47,0.25);
                color:#556B2F;
                border:1px solid #556B2F;
                padding:12px;
                border-radius:8px;
                margin-bottom:8px;">
                <b>{row['title']}</b><br>
                Available
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("Claim this project", key=f"claim_{row['id']}"):
            name = student_name.strip()

            if not name:
                st.warning("Please enter your name first.")

            else:
                already_claimed = pd.read_sql_query(
                    "SELECT * FROM projects WHERE claimed_by=?",
                    conn,
                    params=(name,)
                )

                if len(already_claimed) > 0:
                    st.warning("You already claimed a project. Please give it back first.")

                else:
                    c.execute(
                        "UPDATE projects SET claimed_by=? WHERE id=? AND claimed_by IS NULL",
                        (name, row["id"])
                    )
                    conn.commit()
                    st.rerun()

st.subheader("Current project selection")

overview = pd.read_sql_query(
    """
    SELECT 
        title AS Project,
        claimed_by AS Student
    FROM projects
    ORDER BY title
    """,
    conn
)

overview["Student"] = overview["Student"].fillna("Available")

st.dataframe(
    overview,
    hide_index=True,
    use_container_width=True
)