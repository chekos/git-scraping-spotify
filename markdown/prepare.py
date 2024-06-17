from pandas import read_csv, to_datetime, NamedAgg


def streamlit_theme():
    font = "IBM Plex Mono"
    primary_color = "#F63366"
    font_color = "#262730"
    grey_color = "#f0f2f6"
    base_size = 16
    lg_font = base_size * 1.25
    sm_font = base_size * 0.8  # st.table size
    xl_font = base_size * 1.75

    config = {
        "config": {
            "arc": {"fill": primary_color},
            "area": {"fill": primary_color},
            "circle": {"fill": primary_color, "stroke": font_color, "strokeWidth": 0.5},
            "line": {"stroke": primary_color},
            "path": {"stroke": primary_color},
            "point": {"stroke": primary_color},
            "rect": {"fill": primary_color},
            "shape": {"stroke": primary_color},
            "symbol": {"fill": primary_color},
            "title": {
                "font": font,
                "color": font_color,
                "fontSize": lg_font,
                "anchor": "start",
            },
            "axis": {
                "titleFont": font,
                "titleColor": font_color,
                "titleFontSize": sm_font,
                "labelFont": font,
                "labelColor": font_color,
                "labelFontSize": sm_font,
                "gridColor": grey_color,
                "domainColor": font_color,
                "tickColor": "#fff",
            },
            "header": {
                "labelFont": font,
                "titleFont": font,
                "labelFontSize": base_size,
                "titleFontSize": base_size,
            },
            "legend": {
                "titleFont": font,
                "titleColor": font_color,
                "titleFontSize": sm_font,
                "labelFont": font,
                "labelColor": font_color,
                "labelFontSize": sm_font,
            },
            "range": {
                "category": ["#f63366", "#fffd80", "#0068c9", "#ff2b2b", "#09ab3b"],
                "diverging": [
                    "#850018",
                    "#cd1549",
                    "#f6618d",
                    "#fbafc4",
                    "#f5f5f5",
                    "#93c5fe",
                    "#5091e6",
                    "#1d5ebd",
                    "#002f84",
                ],
                "heatmap": [
                    "#ffb5d4",
                    "#ff97b8",
                    "#ff7499",
                    "#fc4c78",
                    "#ec245f",
                    "#d2004b",
                    "#b10034",
                    "#91001f",
                    "#720008",
                ],
                "ramp": [
                    "#ffb5d4",
                    "#ff97b8",
                    "#ff7499",
                    "#fc4c78",
                    "#ec245f",
                    "#d2004b",
                    "#b10034",
                    "#91001f",
                    "#720008",
                ],
                "ordinal": [
                    "#ffb5d4",
                    "#ff97b8",
                    "#ff7499",
                    "#fc4c78",
                    "#ec245f",
                    "#d2004b",
                    "#b10034",
                    "#91001f",
                    "#720008",
                ],
            },
        }
    }
    return config


def read_tracks(filepath):
    data = read_csv(filepath)
    data["played_at"] = to_datetime(data["played_at"], format='ISO8601', utc = True).dt.tz_convert("US/Pacific")
    data["played_date"] = data["played_at"].dt.date
    data["played_date"] = to_datetime(data["played_date"])

    return data


def clean_artists(df, artist_col="artists"):
    df[artist_col] = (
        df[artist_col]
        .str.replace("Adan", "Adán")
        .str.replace("Iluminatik", "Illuminatik")
    )
    return df


voi = [
    "played_at",
    "played_date",
    "track_name",
    "album_artists",
    "album_artist_name",
    "album_name",
    "track_popularity",
    "track_explicit",
    "track_duration_ms",
    "track_uri",
]

colname_map = {
    "track_name": "song",
    "artists": "artist",
    "track_popularity": "popularity",
    "track_explicit": "is_explicit",
    "track_duration_ms": "duration_ms",
    "track_uri": "uri",
}


def _gen_df(df):
    gen_df = (
        df.drop_duplicates(subset=["artists", "track_name"])
        .drop(columns=["played_at", "played_date", "track_uri"])
        .set_index(["artists", "track_name"])
    )

    step_1 = df.groupby(["artists", "track_name", "track_uri"], as_index=False).agg(
        n=NamedAgg(column="played_at", aggfunc="count")
    )
    step_1 = (
        step_1.sort_values(
            by=["artists", "track_name", "track_uri", "n"], ascending=False
        )
        .drop_duplicates(subset=["artists", "track_name"])
        .set_index(["artists", "track_name"])
    )
    step_1.drop(columns=["n"], inplace=True)

    gen_df = gen_df.join(step_1)
    return gen_df


def _agg_df(df):
    agg_df = df.groupby(["artists", "track_name", "played_date"], as_index=False).agg(
        n=NamedAgg("played_at", "count"),
    )
    first_day_df = agg_df.groupby(["artists", "track_name"]).agg(
        first_day=NamedAgg("played_date", "min"),
        last_day=NamedAgg("played_date", "max"),
    )

    agg_df = agg_df.set_index(["artists", "track_name"]).join(first_day_df)

    agg_df["day_played"] = (agg_df["played_date"] - agg_df["first_day"]).dt.days

    agg_df.reset_index(inplace=True)

    agg_df["cumsum"] = agg_df.groupby(["artists", "track_name"])["n"].cumsum()

    return agg_df


def song_df(filepath, voi=voi):
    data = read_tracks(filepath)[voi]

    data["artists"] = data["album_artists"].str.split(" & ")
    data = data.explode("artists")

    data = clean_artists(data)

    gen_df = _gen_df(data)
    agg_df = _agg_df(data)

    song_df = (
        gen_df.join(agg_df.set_index(["artists", "track_name"]))
        .reset_index()
        .rename(columns=colname_map)
    )

    return song_df

def find_top_artists(songs, n = 10):
    top_artists = songs['artist'].value_counts().reset_index().head(n)
    top_artists.columns = ['artist', 'n_plays']
    return top_artists
