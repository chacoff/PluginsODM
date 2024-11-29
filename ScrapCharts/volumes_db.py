import pandas as pd
from django.shortcuts import render
from django.http import HttpResponseRedirect
from sqlalchemy import create_engine, text

# host.docker.internal
db_url = "postgresql+psycopg2://postgres:API@host.docker.internal:5432/waste_management"


def scrap_params_dev(request):
    engine = create_engine(db_url)
    df = pd.read_sql("SELECT * FROM SCRAP_PARAMS;", con=engine)
    engine.dispose()

    if request.method == "POST":
        action = request.POST.get("action")

        # Handle Update
        if action and action.startswith("update"):
            row_id = int(action.split("_")[1])
            updated_values = {
                col: request.POST.get(f"data_{row_id}_{col_idx}")
                for col_idx, col in enumerate(df.columns)
            }
            query = f"UPDATE SCRAP_PARAMS SET {', '.join([f'{k} = %s' for k in updated_values.keys()])} WHERE id = %s;"
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(query, *updated_values.values(), updated_values["id"])
            engine.dispose()

        # Handle Delete
        elif action and action.startswith("delete"):
            row_id = int(action.split("_")[1])
            query = f"DELETE FROM SCRAP_PARAMS WHERE id = %s;"
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(query, row_id)
            engine.dispose()

        # Handle Add
        elif action == "add":
            new_row = request.POST.get("new_row").split(",")
            query = "INSERT INTO SCRAP_PARAMS VALUES (%s);"
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(query, tuple(new_row))
            engine.dispose()

        # return HttpResponseRedirect(request.path)

    return df.to_dict(orient="split")
    # return render(request, "scrap_params.html", {"df": df.to_dict(orient="split")})
