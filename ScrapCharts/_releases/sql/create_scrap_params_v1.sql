CREATE TABLE public.SCRAP_PARAMS (
    counter SERIAL PRIMARY KEY,
    sector VARCHAR(20) NOT NULL,
    angle INTEGER,
    crop_left INTEGER,
    crop_top INTEGER,
    crop_right INTEGER,
    crop_bottom INTEGER,
    scale FLOAT,
    quality INTEGER,
    reviewer VARCHAR(40),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (sector)
);