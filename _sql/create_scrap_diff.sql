CREATE TABLE public.SCRAP_DIFF (
    counter SERIAL PRIMARY KEY,
    task_id VARCHAR(40) NOT NULL,
    flightDay TIMESTAMP NOT NULL,
    factory VARCHAR(15) NOT NULL,
    sector VARCHAR(50) NOT NULL,
    pile VARCHAR(20) NOT NULL,
    base_method VARCHAR(50) NOT NULL,
    base_reference FLOAT,
    volume_drone FLOAT,
    volume_trench FLOAT,
    volume_total FLOAT,
    area FLOAT,
    perimeter FLOAT,
    pilot VARCHAR(80),
    reviewer VARCHAR(80),
    polygon TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
