-- Generated offline from backend/models.py; do not edit by hand.
-- Regenerate: python database/generate_postgres_schema.py
-- Verify: python database/generate_postgres_schema.py --check
-- Proposal for an EMPTY application schema only; execution requires authorization.
-- Plain CREATE statements intentionally fail if objects already exist.
-- Client-side Python defaults are not SQL server defaults.
-- Existing databases require a separately reviewed migration, not this file.

CREATE TABLE users (
	id SERIAL NOT NULL,
	name VARCHAR(100),
	email VARCHAR(150),
	role VARCHAR(30),
	avatar_url VARCHAR(255),
	created_at TIMESTAMP WITHOUT TIME ZONE,
	PRIMARY KEY (id),
	UNIQUE (email)
);

CREATE TABLE audit_logs (
	id SERIAL NOT NULL,
	user_id INTEGER,
	action VARCHAR(80) NOT NULL,
	details TEXT,
	ip_address VARCHAR(45),
	timestamp TIMESTAMP WITHOUT TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE trends (
	trend_id SERIAL NOT NULL,
	keyword VARCHAR(100) NOT NULL,
	platform VARCHAR(20) NOT NULL,
	total_views BIGINT,
	growth_rate FLOAT,
	virality_score FLOAT,
	peak_date TIMESTAMP WITHOUT TIME ZONE,
	created_by INTEGER,
	timestamp TIMESTAMP WITHOUT TIME ZONE,
	observation_key VARCHAR(64),
	first_seen_at TIMESTAMP WITHOUT TIME ZONE,
	last_seen_at TIMESTAMP WITHOUT TIME ZONE,
	scan_count INTEGER,
	current_trend_score FLOAT,
	current_direction VARCHAR(20),
	current_confidence VARCHAR(20),
	current_velocity FLOAT,
	current_acceleration FLOAT,
	PRIMARY KEY (trend_id),
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_trends_observation_key ON trends (observation_key);

CREATE TABLE metrics (
	id SERIAL NOT NULL,
	trend_id INTEGER NOT NULL,
	views BIGINT,
	likes BIGINT,
	shares BIGINT,
	comments_count BIGINT,
	recorded_date DATE,
	captured_at TIMESTAMP WITHOUT TIME ZONE,
	engagement_rate FLOAT,
	source VARCHAR(50),
	PRIMARY KEY (id),
	FOREIGN KEY(trend_id) REFERENCES trends (trend_id)
);

CREATE TABLE reports (
	report_id SERIAL NOT NULL,
	trend_id INTEGER NOT NULL,
	generated_by INTEGER,
	format VARCHAR(10),
	file_path VARCHAR(255),
	gen_date TIMESTAMP WITHOUT TIME ZONE,
	PRIMARY KEY (report_id),
	FOREIGN KEY(trend_id) REFERENCES trends (trend_id),
	FOREIGN KEY(generated_by) REFERENCES users (id)
);

CREATE TABLE sentiment (
	id SERIAL NOT NULL,
	trend_id INTEGER NOT NULL,
	positive_score FLOAT,
	negative_score FLOAT,
	neutral_score FLOAT,
	dominant_sentiment VARCHAR(20),
	sample_comment TEXT,
	PRIMARY KEY (id),
	FOREIGN KEY(trend_id) REFERENCES trends (trend_id)
);
