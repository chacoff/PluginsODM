INSERT INTO public.SCRAP_PARAMS (
    sector, angle, crop_left, crop_top, crop_right, crop_bottom, scale, quality, reviewer, updated_at
)
VALUES (
    'SectorA', 45, 10, 20, 30, 40, 0.85, 90, 'Jaime', '2024-11-29 21:30:00'
)
ON CONFLICT (sector)
DO UPDATE SET
    angle = EXCLUDED.angle,
    crop_left = EXCLUDED.crop_left,
    crop_top = EXCLUDED.crop_top,
    crop_right = EXCLUDED.crop_right,
    crop_bottom = EXCLUDED.crop_bottom,
    scale = EXCLUDED.scale,
    quality = EXCLUDED.quality,
    reviewer = EXCLUDED.reviewer,
    updated_at = EXCLUDED.updated_at
WHERE (
    SCRAP_PARAMS.angle IS DISTINCT FROM EXCLUDED.angle OR
    SCRAP_PARAMS.crop_left IS DISTINCT FROM EXCLUDED.crop_left OR
    SCRAP_PARAMS.crop_top IS DISTINCT FROM EXCLUDED.crop_top OR
    SCRAP_PARAMS.crop_right IS DISTINCT FROM EXCLUDED.crop_right OR
    SCRAP_PARAMS.crop_bottom IS DISTINCT FROM EXCLUDED.crop_bottom OR
    SCRAP_PARAMS.scale IS DISTINCT FROM EXCLUDED.scale OR
    SCRAP_PARAMS.quality IS DISTINCT FROM EXCLUDED.quality OR
    SCRAP_PARAMS.reviewer IS DISTINCT FROM EXCLUDED.reviewer OR
    SCRAP_PARAMS.updated_at IS DISTINCT FROM EXCLUDED.updated_at
);