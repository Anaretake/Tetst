import sqlite3

def initialize_interpretation_data(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS interpretation_ranges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        interpretation TEXT NOT NULL,
        range_start REAL NOT NULL,
        range_end REAL NOT NULL
    )''')

    cursor.execute("SELECT COUNT(*) FROM interpretation_ranges")
    count = cursor.fetchone()[0]

    if count == 0:
        ranges = [
            ("reaction_speed", "Отличная скорость реакции", 0, 525),
            ("reaction_speed", "Хорошая скорость реакции", 526, 580),
            ("reaction_speed", "Допустимые показатели, возможно лёгкое утомление", 581, 600),
            ("reaction_speed", "Замедленная реакция, возможно утомление", 601, float("inf")),
            ("std_deviation", "Очень высокая стабильность внимания", 0, 90),
            ("std_deviation", "Незначительные колебания внимания", 91, 130),
            ("std_deviation", "Выраженная нестабильность внимания", 131, 165),
            ("std_deviation", "Высокая нестабильность, возможно утомление", 166, float("inf")),
            ("accuracy", "Отличная концентрация, высокая безошибочность", 98, 100),
            ("accuracy", "Незначительное количество ошибок, хорошее внимание", 94, 97.99),
            ("accuracy", "Умеренное количество ошибок, возможно утомление", 90, 93.99),
            ("accuracy", "Большое количество ошибок, возможно утомление", 0, 89.99)
        ]
        cursor.executemany('''INSERT INTO interpretation_ranges (category, interpretation, range_start, range_end)
                              VALUES (?, ?, ?, ?)''', ranges)
def init_db():
    conn = sqlite3.connect("test_app.db")
    cursor = conn.cursor()
    #cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            patronymic TEXT NOT NULL,
            age INTEGER NOT NULL
        )
    """)
    #cursor.execute("DROP TABLE IF EXISTS test_results")
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS test_results (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           test_date TEXT NOT NULL,
           user_id INTEGER NOT NULL,
           correct_answers INTEGER NOT NULL,
           incorrect_answers INTEGER NOT NULL,
           score_indicator REAL NOT NULL,
           tracking_indicator REAL NOT NULL,
           integral_indicator REAL NOT NULL,
            ball_score INTEGER,
            ball_comment TEXT,
           FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
       )
       """)
    #cursor.execute("DROP TABLE IF EXISTS test_results_reaction_test")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_results_reaction_test (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_date            TEXT NOT NULL,
            user_id INTEGER        NOT NULL,
            avg_reaction_time REAL NOT NULL,
            std_deviation      REAL NOT NULL,
            accuracy_percent   REAL NOT NULL,
            full_interpretation TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)
    #cursor.execute("DROP TABLE IF EXISTS test_results_krepelin_test")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_results_krepelin_test (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_date TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            K_work REAL NOT NULL,
            error_count INTEGER NOT NULL,
            interpret_results TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)
    # cursor.execute("DROP TABLE IF EXISTS test_results_san_test")
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results_san_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_date TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                samocuvstvie REAL,
                aktivnost REAL,
                nastroenie REAL,
                samocuvstvie_state TEXT,
                aktivnost_state TEXT,
                nastroenie_state TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS interpretation_ranges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,             -- 'reaction_speed', 'std_deviation', or 'accuracy'
                interpretation TEXT NOT NULL,
                range_start REAL NOT NULL,
                range_end REAL NOT NULL
            )
        """)
    # cursor.execute("DROP TABLE IF EXISTS test_results_simple_reaction")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_results_simple_reaction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_date TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            avg_reaction_time REAL,
            std_deviation REAL,
            wippl_coefficient REAL,
            interpretation TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS full_test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_date TEXT NOT NULL,
            user_id INTEGER NOT NULL,

            adaptive_model_result TEXT,         -- Баллы + интерпретация АМОD
            complex_reaction_result TEXT,        -- Интерпретация СЗМР
            simple_reaction_result TEXT,         -- Интерпретация ПЗМР
            krepelin_result TEXT,                -- Интерпретация Крепелина
            san_result TEXT,                     -- Интерпретации по САН (Самочувствие, Активность, Настроение)

            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
           CREATE TABLE IF NOT EXISTS normalization_stats (
               key TEXT PRIMARY KEY,
               value REAL
           )
       """)
    cursor.execute("""
          CREATE TABLE IF NOT EXISTS qfol_raw_data (
              user_id INTEGER,
              qfol_value REAL,
              timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
          )
      """)
    cursor.execute("SELECT COUNT(*) FROM normalization_stats WHERE key = 'qfol_empirical_coefficient'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
               INSERT INTO normalization_stats (key, value)
               VALUES (?, ?)
           """, ("qfol_empirical_coefficient", 20000))
    initialize_interpretation_data(cursor)
    cursor.execute('''
          CREATE TABLE IF NOT EXISTS settings (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              password TEXT NOT NULL
          )
      ''')
    cursor.execute('SELECT COUNT(*) FROM settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO settings (password) VALUES (?)', ('1234',))

    conn.commit()
    conn.close()


