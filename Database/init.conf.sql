-- 1. Пользователи
CREATE TABLE userhub (
    id            INT PRIMARY KEY,
    name          TEXT,
    tstart        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    balance       INT,
    is_reg        BOOLEAN  DEFAULT FALSE,
    refferer_id   INT,
    CONSTRAINT fk_userhub_refferer
        FOREIGN KEY (refferer_id) REFERENCES userhub(id)
);

-- 2. Транзакции
CREATE TABLE transactions (
    id      SERIAL PRIMARY KEY,
    price   INT  NOT NULL,
    action  TEXT,
    ts      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Функциональные сообщения / ответы
CREATE TABLE pfunc (
    id        SERIAL PRIMARY KEY,
    message   TEXT NOT NULL,
    cls       TEXT,
    answer    TEXT NOT NULL,
    user_id   INT  NOT NULL,
    ts        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    position  TEXT,
    pay_id    INT  NOT NULL,
    CONSTRAINT fk_pfunc_user
        FOREIGN KEY (user_id) REFERENCES userhub(id),
    CONSTRAINT fk_pfunc_payment
        FOREIGN KEY (pay_id)  REFERENCES transactions(id)
);

-- 4. Задания
CREATE TABLE tasks (
    id        SERIAL PRIMARY KEY,
    user_id   INT  NOT NULL,
    ts        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    test      TEXT NOT NULL,
    date      TIMESTAMP NOT NULL,
    is_active BOOLEAN NOT NULL,
    CONSTRAINT fk_tasks_user
        FOREIGN KEY (user_id) REFERENCES userhub(id)
);

-- 5. Логи сессий
CREATE TABLE spylog (
    id       SERIAL PRIMARY KEY,
    user_id  INT  NOT NULL,
    action  TEXT NOT NULL,
    ts   TIMESTAMP NOT NULL,
    CONSTRAINT fk_spylog_user
        FOREIGN KEY (user_id) REFERENCES userhub(id)
);

CREATE ROLE app WITH LOGIN PASSWORD 'YOUR PASSWORD';

-- 4) Даём доступ к схеме (по умолчанию public)
GRANT USAGE ON SCHEMA public TO app;

-- 5) Права на ВСЕ существующие таблицы
GRANT SELECT, INSERT, UPDATE, DELETE
      ON ALL TABLES IN SCHEMA public
      TO app;

-- 6) Права на ВСЕ существующие последовательности
--    USAGE – вызов nextval(); SELECT – currval(); UPDATE – setval()
GRANT USAGE, SELECT, UPDATE
      ON ALL SEQUENCES IN SCHEMA public
      TO app;

-- 7) Автоматические права на объекты,
--    которые будут создаваться в будущем (ALEMBIC, init_db() и т.д.)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
      GRANT SELECT, INSERT, UPDATE, DELETE
      ON TABLES TO app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
      GRANT USAGE, SELECT, UPDATE
      ON SEQUENCES TO app;
