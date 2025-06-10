from backend.model.db_connect import mysql_pool

def create_table(query: str):
    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        print("建表失敗:", e)
    finally:
        cursor.close()
        conn.close()

#使用者表單
create_table("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        phone VARCHAR(20) NOT NULL UNIQUE,
        is_phone_verified TINYINT(1) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
""")

#公立收容所認養表單
create_table("""
    CREATE TABLE IF NOT EXISTS public(
        animal_subid VARCHAR(50) NOT NULL UNIQUE PRIMARY KEY,
        animal_place VARCHAR(50) NOT NULL,
        animal_kind  VARCHAR(50) NOT NULL,
        album_file TEXT NOT NULL,
        animal_sex VARCHAR(20) NOT NULL,
        animal_bodytype VARCHAR(10) NOT NULL,
        animal_colour VARCHAR(20) NOT NULL,
        shelter_address VARCHAR(255) NOT NULL,
        shelter_tel VARCHAR(50) NOT NULL
    );
""") 

#送養表單
create_table( """
    CREATE TABLE IF NOT EXISTS send (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        pet_name VARCHAR(255) NOT NULL,
        pet_breed VARCHAR(50) NOT NULL,
        pet_kind VARCHAR(50) NOT NULL,
        pet_sex VARCHAR(50) NOT NULL,
        pet_bodytype VARCHAR(50) NOT NULL,
        pet_colour VARCHAR(50) NOT NULL,
        pet_place VARCHAR(50) NOT NULL,
        pet_describe VARCHAR(255) NOT NULL,
        pet_ligation_status VARCHAR(50) NOT NULL,
        pet_age VARCHAR(50) NOT NULL,
        created_at DATE DEFAULT (CURRENT_DATE),
        CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    );
""")

create_table("""
    CREATE TABLE IF NOT EXISTS imgurl(
        id INT AUTO_INCREMENT PRIMARY KEY,
        send_id INT NOT NULL,
        img_url VARCHAR(255) NOT NULL,
        FOREIGN KEY (send_id) REFERENCES send(id) ON DELETE CASCADE
    );
""")

create_table( """
    CREATE TABLE IF NOT EXISTS likes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL, 
        send_id INT NOT NULL,  
        liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_likes_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT fk_likes_send FOREIGN KEY (send_id) REFERENCES send(id) ON DELETE CASCADE
    );
""")

create_queries = [
    # 1. forms
    """
    CREATE TABLE IF NOT EXISTS forms (
      id         INT AUTO_INCREMENT PRIMARY KEY,
      post_id    INT            NOT NULL UNIQUE,
      title      VARCHAR(255)   NOT NULL,
      created_at DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (post_id) REFERENCES send(id) ON DELETE CASCADE
    );
    """,
    # 2. form_questions
    """
    CREATE TABLE IF NOT EXISTS form_questions (
      id               INT AUTO_INCREMENT PRIMARY KEY,
      form_id          INT            NOT NULL,
      question_key     VARCHAR(50)    NOT NULL,
      question_order   INT            NOT NULL,
      type             ENUM('text','choice','image') NOT NULL,
      title            VARCHAR(255)   NOT NULL,
      is_required      TINYINT(1)     NOT NULL  DEFAULT 1,
      FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE,
      UNIQUE KEY uq_form_q_order (form_id, question_order),
      INDEX (question_key)
    );
    """,
    # 3. question_options
    """
    CREATE TABLE IF NOT EXISTS question_options (
      id             INT AUTO_INCREMENT PRIMARY KEY,
      question_id    INT            NOT NULL,
      option_order   INT            NOT NULL,
      label          VARCHAR(255)   NOT NULL,
      value          VARCHAR(255),
      FOREIGN KEY (question_id) REFERENCES form_questions(id) ON DELETE CASCADE,
      INDEX (question_id)
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS form_submissions (
      id                INT AUTO_INCREMENT PRIMARY KEY,
      form_id           INT            NOT NULL,       -- FK → forms(id)
      submitter_user_id INT            NULL,           -- FK → users(id)
      submitted_at      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE,
      FOREIGN KEY (submitter_user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS form_answers (
      id                  INT AUTO_INCREMENT PRIMARY KEY,
      submission_id       INT            NOT NULL,     -- FK → form_submissions(id)
      question_id         INT            NOT NULL,     -- FK → form_questions(id)
      answer_text         TEXT           NULL,
      answer_option_id    INT            NULL,
      image_url           TEXT           NULL,
      FOREIGN KEY (submission_id)    REFERENCES form_submissions(id) ON DELETE CASCADE,
      FOREIGN KEY (question_id)      REFERENCES form_questions(id)   ON DELETE CASCADE,
      FOREIGN KEY (answer_option_id) REFERENCES question_options(id) ON DELETE SET NULL
    );
    """
]
for sql in create_queries:
    create_table(sql)