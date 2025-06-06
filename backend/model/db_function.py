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

create_table(
""" CREATE TABLE forms (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,             
  description TEXT,                           
  created_by BIGINT NOT NULL,                 
  created_at DATETIME NOT NULL DEFAULT NOW(),
  updated_at DATETIME NOT NULL DEFAULT NOW() ON UPDATE NOW(),
  is_published TINYINT(1) NOT NULL DEFAULT 0 
);
"""
)

create_table("""
CREATE TABLE form_fields (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  form_id BIGINT NOT NULL,            
  label VARCHAR(500) NOT NULL,        
  `type` VARCHAR(50) NOT NULL,       
  placeholder VARCHAR(255) NULL,       
  is_required TINYINT(1) NOT NULL DEFAULT 0,
  sort_order INT NOT NULL DEFAULT 0,   
  extra JSON NULL,                     
  created_at DATETIME NOT NULL DEFAULT NOW(),
  updated_at DATETIME NOT NULL DEFAULT NOW() ON UPDATE NOW(),
  INDEX (form_id),
  FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE
);
""")


create_table("""
CREATE TABLE form_field_options (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  field_id BIGINT NOT NULL,    
  `value` VARCHAR(500) NOT NULL, 
  `label` VARCHAR(500) NOT NULL, 
  sort_order INT NOT NULL DEFAULT 0,
  INDEX (field_id),
  FOREIGN KEY (field_id) REFERENCES form_fields(id) ON DELETE CASCADE
);
""")

create_table("""
CREATE TABLE responses (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  form_id BIGINT NOT NULL,          
  respondent_id BIGINT NULL,        
  submitted_at DATETIME NOT NULL DEFAULT NOW(),
  INDEX (form_id),
  FOREIGN KEY (form_id) REFERENCES forms(id) ON DELETE CASCADE
);
""")


create_table("""
CREATE TABLE response_answers (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  response_id BIGINT NOT NULL,      
  field_id BIGINT NOT NULL,         
  answer_text TEXT NULL,            
  answer_option_id BIGINT NULL,     
  answer_options JSON NULL,         
  uploaded_files JSON NULL,         
  INDEX (response_id),
  INDEX (field_id),
  FOREIGN KEY (response_id) REFERENCES responses(id) ON DELETE CASCADE,
  FOREIGN KEY (field_id) REFERENCES form_fields(id) ON DELETE CASCADE
);

""")

