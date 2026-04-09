-- Tabel 1: nodes
CREATE TABLE nodes (
    node_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_name       VARCHAR(100) NOT NULL UNIQUE,
    ip_address      VARCHAR(45)  NOT NULL,
    port            INTEGER      NOT NULL DEFAULT 5001,
    role            VARCHAR(20)  NOT NULL DEFAULT 'worker',
    status          VARCHAR(20)  NOT NULL DEFAULT 'active',
    last_heartbeat  TIMESTAMP    NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_role   CHECK (role IN ('coordinator','worker')),
    CONSTRAINT chk_status CHECK (status IN ('active','failed','recovering','offline'))
);
CREATE INDEX idx_nodes_status ON nodes(status);
CREATE INDEX idx_nodes_heartbeat ON nodes(last_heartbeat);

-- Tabel 2: checkpoint_sessions
CREATE TABLE checkpoint_sessions (
    session_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_type   VARCHAR(30) NOT NULL,
    global_status  VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    total_nodes    INTEGER NOT NULL,
    acked_nodes    INTEGER NOT NULL DEFAULT 0,
    started_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at   TIMESTAMP,
    notes          TEXT
);

-- Tabel 3: checkpoints
CREATE TABLE checkpoints (
    checkpoint_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id          UUID NOT NULL REFERENCES nodes(node_id),
    session_id       UUID REFERENCES checkpoint_sessions(session_id),
    sequence_number  INTEGER NOT NULL,
    file_path        TEXT    NOT NULL,
    file_size_kb     INTEGER,
    checksum         VARCHAR(64),
    status           VARCHAR(20) NOT NULL DEFAULT 'valid',
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_node_seq UNIQUE (node_id, sequence_number)
);
CREATE INDEX idx_ckpt_node    ON checkpoints(node_id);
CREATE INDEX idx_ckpt_session ON checkpoints(session_id);
CREATE INDEX idx_ckpt_status  ON checkpoints(status);

-- Tabel 4: recovery_logs
CREATE TABLE recovery_logs (
    recovery_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id       UUID REFERENCES checkpoint_sessions(session_id),
    checkpoint_id    UUID NOT NULL REFERENCES checkpoints(checkpoint_id),
    trigger_reason   TEXT NOT NULL,
    affected_nodes   TEXT[],
    status           VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    recovery_time_ms INTEGER,
    data_loss_ms     INTEGER,
    started_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at      TIMESTAMP,
    error_detail     TEXT
);

-- Tabel 5: task_states
CREATE TABLE task_states (
    task_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id         UUID NOT NULL REFERENCES nodes(node_id),
    checkpoint_id   UUID NOT NULL REFERENCES checkpoints(checkpoint_id),
    task_name       VARCHAR(200) NOT NULL,
    state_data      JSONB NOT NULL,
    progress_pct    SMALLINT DEFAULT 0 CHECK (progress_pct BETWEEN 0 AND 100),
    status          VARCHAR(20) NOT NULL DEFAULT 'checkpointed',
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_task_state_data ON task_states USING GIN (state_data);
CREATE INDEX idx_task_node       ON task_states(node_id);
CREATE INDEX idx_task_checkpoint ON task_states(checkpoint_id);