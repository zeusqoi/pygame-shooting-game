import pymysql
import db_config
import threading


class DBManager:
    def __init__(self):
        self.host = db_config.DB_HOST
        self.user = db_config.DB_USER
        self.password = db_config.DB_PASSWORD
        self.db_name = db_config.DB_NAME
        self.conn = None
        self.is_connecting = True

        # Connect in a background thread to prevent UI freezing
        threading.Thread(target=self._connect, daemon=True).start()

    def _connect(self):
        try:
            self.conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db_name,
                charset='utf8mb4',
                connect_timeout=3
            )
            print("DB 연결 성공")
            self._create_tables()
        except Exception as e:
            print(f"DB 연결 실패 (로컬 임시 모드로 동작): {e}")
            self.conn = None
        finally:
            self.is_connecting = False

    def _create_tables(self):
        if not self.conn:
            return
        try:
            with self.conn.cursor() as cursor:

                cursor.execute("""
                               CREATE TABLE IF NOT EXISTS users
                               (
                                   id
                                   INT
                                   AUTO_INCREMENT
                                   PRIMARY
                                   KEY,
                                   username
                                   VARCHAR
                               (
                                   50
                               ) UNIQUE NOT NULL,
                                   password VARCHAR
                               (
                                   255
                               ) NOT NULL,
                                   nickname VARCHAR
                               (
                                   50
                               ) UNIQUE NOT NULL,
                                   email VARCHAR
                               (
                                   255
                               ) DEFAULT NULL,
                                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                               """)

                cursor.execute("""
                               CREATE TABLE IF NOT EXISTS game_settings
                               (
                                   setting_id
                                   INT
                                   AUTO_INCREMENT
                                   PRIMARY
                                   KEY,
                                   user_id
                                   INT
                                   UNIQUE
                                   NOT
                                   NULL,
                                   master_volume
                                   INT
                                   DEFAULT
                                   100,
                                   FOREIGN
                                   KEY
                               (
                                   user_id
                               ) REFERENCES users
                               (
                                   id
                               ) ON DELETE CASCADE
                                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                               """)

                cursor.execute("""
                               CREATE TABLE IF NOT EXISTS ranking
                               (
                                   id
                                   INT
                                   AUTO_INCREMENT
                                   PRIMARY
                                   KEY,
                                   user_id
                                   INT
                                   NULL,
                                   guest_name
                                   VARCHAR
                               (
                                   50
                               ) DEFAULT NULL,
                                   score INT NOT NULL,
                                   game_mode ENUM
                               (
                                   'Single',
                                   'Duo'
                               ) NOT NULL,
                                   play_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                   FOREIGN KEY
                               (
                                   user_id
                               ) REFERENCES users
                               (
                                   id
                               ) ON DELETE SET NULL
                                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                               """)
            self.conn.commit()

            # 기존 테이블 호환성을 위한 email 컬럼 추가 시도
            try:
                with self.conn.cursor() as cursor:
                    cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255) DEFAULT NULL;")
                self.conn.commit()
            except Exception:
                pass  # 이미 컬럼이 존재하면 무시

            print("모든 테이블 생성/확인 완료")
        except Exception as e:
            print(f"테이블 생성 오류: {e}")

    def register(self, username, password, nickname, email=None):
        if not self.conn: return False
        try:
            with self.conn.cursor() as cursor:
                sql = "INSERT INTO users (username, password, nickname, email) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (username, password, nickname, email))

                user_id = self.conn.insert_id()
                cursor.execute("INSERT INTO game_settings (user_id) VALUES (%s)", (user_id,))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"회원가입 실패: {e}")
            return False

    def check_id_duplicate(self, username):
        if not self.conn: return False  # 오프라인 모드에서는 중복이 없는 것으로 간주 (가입 허용)
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"중복 확인 실패: {e}")
            return False

    def login(self, username, password):
        # 1. DB가 연결되지 않았을 때의 처리
        if not self.conn:
            # 개발용 임시 계정 (admin / 1234)
            if username == "admin" and password == "1234":
                print("임시 모드: admin 계정 로그인 성공")
                return True

            # DB가 없으면 일반적인 경우에는 로그인을 막아야 합니다.
            print("DB 연결 없음: 로그인 불가")
            return False

            # 2. DB가 연결되어 있을 때의 실제 검사
        try:
            with self.conn.cursor() as cursor:
                # SQL 쿼리로 아이디와 비밀번호가 일치하는지 확인
                cursor.execute("SELECT id, nickname FROM users WHERE username=%s AND password=%s", (username, password))
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            print(f"로그인 쿼리 실행 중 오류: {e}")
            return False

    def save_score(self, score, username=None, user_id=None, game_mode="Single"):
        if not self.conn: return
        try:
            with self.conn.cursor() as cursor:
                sql = "INSERT INTO ranking (user_id, guest_name, score, game_mode) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (user_id, username, score, game_mode))
            self.conn.commit()
            print(f"점수 저장 완료: {score} ({game_mode})")
        except Exception as e:
            print(f"점수 저장 실패: {e}")

    def get_rankings(self, mode=None, limit=10):

        query = """
                SELECT COALESCE(u.nickname, r.guest_name) AS display_name, \
                       MAX(r.score)                       AS max_score, \
                       r.game_mode, \
                       MAX(r.play_date)                   AS latest_play_date
                FROM ranking r
                         LEFT JOIN users u ON r.user_id = u.id
                """

        # 2. 모드(Single/Duo) 필터링
        if mode:
            query += " WHERE r.game_mode = %s "

        # 3. 그룹화 및 정렬
        query += " GROUP BY display_name, r.game_mode ORDER BY max_score DESC "

        if limit:
            query += f" LIMIT {limit} "

        try:
            with self.conn.cursor() as cursor:
                if mode:
                    cursor.execute(query, (mode,))
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"내 랭킹 가져오기 실패: {e}")
            return []

    def get_user_ranking(self, username, mode=None):
        if not self.conn or not username:
            return None, None
        try:
            with self.conn.cursor() as cursor:
                target_name = "Guest"
                if username != "Guest":
                    cursor.execute("SELECT nickname FROM users WHERE username=%s", (username,))
                    user_row = cursor.fetchone()
                    if not user_row:
                        return None, None
                    target_name = user_row[0]

                all_ranks = self.get_rankings(mode=mode, limit=None)
                best_score = None
                best_rank = None

                for idx, row in enumerate(all_ranks):
                    if row[0] == target_name:
                        if best_score is None:
                            best_score = row[1]
                            best_rank = idx + 1
                            break

                return best_rank, best_score
        except Exception as e:
            print(f"내 랭킹 가져오기 실패: {e}")
            return None, None