import altair as alt
from prepare import song_df 

alt.data_transformers.disable_max_rows()

songs = song_df("tracks.csv")

def listening_chart(artist="La Banda Baston", df=songs):
    datum_filter = f"datum.artist == '{artist}'"

    n_albums = len(df[df["artist"] == artist]["album_name"].unique())
    n_songs = len(df[df["artist"] == artist]["song"].unique())
    longest_song = df[df["artist"] == artist]["song"].str.len().max()
    name_len = len(artist)
    chart_width = 400

    base = alt.Chart(df).transform_filter(datum_filter)

    peralbum = (
        base.mark_circle(opacity=0.55)
        .encode(
            x=alt.X("played_date", axis=None, stack=None),
            y=alt.Y(
                "album_name:O",
                title="",
                axis=alt.Axis(
                    domain=False,
                    tickOpacity=0,
                ),
            ),
            color=alt.Color(
                "album_name",
                title="",
            ),
            size=alt.Size("count()", title="", legend=None),
        )
        .properties(height=11 * n_albums, width = chart_width)
    )

    persong = (
        base.mark_circle()
        .encode(
            x=alt.X(
                "played_date",
                axis=alt.Axis(
                    orient="top",
                    title="",
                    domain=False,
                    tickOpacity=0,
                    gridColor="#777777",
                    gridOpacity=0.5,
                ),
            ),
            y=alt.Y(
                "song",
                sort="color",
                title="",
                axis=alt.Axis(
                    domainOpacity=0.5,
                    tickOpacity=0,
                    grid=True,
                    gridOpacity=0.5,
                    gridDash=[3, 5],
                ),
            ),
            color=alt.Color("album_name", title="", legend=None),
            size = alt.Size("n:Q")
        )
        .properties(width=chart_width, height = 12 * n_songs)
    )

    final = (
        alt.vconcat(peralbum, persong)
        .properties(title=artist)
        .configure_view(strokeWidth=0)
        .configure_title(
            fontSize=20,
            dy=-20,
            dx=longest_song + (chart_width // 2) + (name_len // 2),
            baseline = "bottom",
        )
        .configure_legend(orient="left", offset=50)
    )
    return final


listening_chart()
