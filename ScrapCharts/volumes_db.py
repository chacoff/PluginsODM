import pandas as pd
from sqlalchemy import create_engine, text, CursorResult
from datetime import datetime

# host.docker.internal
db_url = "postgresql+psycopg2://postgres:API@host.docker.internal:5432/waste_management"


def get_scrap_params(request) -> dict:
    """ gets all the parameters from scrap_params table """

    engine = create_engine(db_url)
    df = pd.read_sql("SELECT * FROM SCRAP_PARAMS;", con=engine)
    engine.dispose()

    df['updated_at'] = df['updated_at'].dt.strftime('%Y-%m-%dT%H:%M:%S')

    return df.to_dict(orient="split")  # records might be better


def insert_to_scrap_params(data: list[any]) -> None:
    """ Insert or update scrap parameters in the database """

    engine = create_engine(db_url)

    try:
        with engine.begin() as connection:
            for i, d in enumerate(data, 1):
                d_values = list(d.values())

                query = """
                INSERT INTO public.SCRAP_PARAMS (
                    sector, angle, crop_left, crop_top, crop_right, crop_bottom, 
                    scale, quality, reviewer, updated_at
                )
                VALUES (
                    :sector, :angle, :crop_left, :crop_top, :crop_right, :crop_bottom, 
                    :scale, :quality, :reviewer, :updated_at
                )
                ON CONFLICT (sector) DO UPDATE SET
                    angle = EXCLUDED.angle,
                    crop_left = EXCLUDED.crop_left,
                    crop_top = EXCLUDED.crop_top,
                    crop_right = EXCLUDED.crop_right,
                    crop_bottom = EXCLUDED.crop_bottom,
                    scale = EXCLUDED.scale,
                    quality = EXCLUDED.quality,
                    reviewer = EXCLUDED.reviewer,
                    updated_at = EXCLUDED.updated_at
                WHERE 
                    SCRAP_PARAMS.angle IS DISTINCT FROM EXCLUDED.angle OR
                    SCRAP_PARAMS.crop_left IS DISTINCT FROM EXCLUDED.crop_left OR
                    SCRAP_PARAMS.crop_top IS DISTINCT FROM EXCLUDED.crop_top OR
                    SCRAP_PARAMS.crop_right IS DISTINCT FROM EXCLUDED.crop_right OR
                    SCRAP_PARAMS.crop_bottom IS DISTINCT FROM EXCLUDED.crop_bottom OR
                    SCRAP_PARAMS.scale IS DISTINCT FROM EXCLUDED.scale OR
                    SCRAP_PARAMS.quality IS DISTINCT FROM EXCLUDED.quality OR
                    SCRAP_PARAMS.reviewer IS DISTINCT FROM EXCLUDED.reviewer OR
                    SCRAP_PARAMS.updated_at IS DISTINCT FROM EXCLUDED.updated_at;
                """

                try:
                    connection.execute(
                        text(query),
                        {
                            "sector": d_values[0],
                            "angle": d_values[1],
                            "crop_left": d_values[2],
                            "crop_top": d_values[3],
                            "crop_right": d_values[4],
                            "crop_bottom": d_values[5],
                            "scale": d_values[6],
                            "quality": d_values[7],
                            "reviewer": d_values[8],
                            "updated_at": d_values[9]  # datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                    )
                except Exception as inner_e:
                    print(f'Error processing record {i}: {inner_e}')

        print('Batch insertion completed successfully')

    except Exception as e:
        print(f'Critical error during database operation: {e}')
    finally:
        engine.dispose()


def delete_scrap_param_row(sector: str) -> CursorResult:
    """ delete a row of scrap parameters according the sector """

    engine = create_engine(db_url)

    with engine.connect() as connection:
        delete_query = text("DELETE FROM public.SCRAP_PARAMS WHERE sector = :sector")
        result = connection.execute(delete_query, {'sector': sector})

        connection.commit()

    return result
