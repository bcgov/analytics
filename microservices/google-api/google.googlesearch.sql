DROP TABLE IF EXISTS google.googlesearch;
CREATE TABLE IF NOT EXISTS google.googlesearch (
	site    VARCHAR(255)    ENCODE ZSTD,
	date    date,
	query   VARCHAR(2047)    ENCODE ZSTD,
	country VARCHAR(255)    ENCODE ZSTD,
	device  VARCHAR(255)    ENCODE ZSTD,
	page    VARCHAR(2047)    ENCODE ZSTD,
	position FLOAT,
	clicks   INTEGER,
	ctr      FLOAT,
	impressions INTEGER
);
ALTER TABLE google.googlesearch OWNER TO microservice;
GRANT SELECT ON TABLE google.googlesearch TO LOOKER; 
