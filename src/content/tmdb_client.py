import requests
import logging
from typing import Dict, List, Any, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class TMDBClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TMDB_API_KEY
        self.base_url = settings.TMDB_BASE_URL
        self.image_base_url = settings.TMDB_IMAGE_BASE_URL
        self._genre_map: Dict[int, str] = {}
        if self.api_key:
            self._load_genres()

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            logger.warning("No TMDB API Key provided. Returning empty response.")
            return None
        
        url = f"{self.base_url}{endpoint}"
        query_params = {"api_key": self.api_key, "language": "en-US"}
        if params:
            query_params.update(params)

        try:
            resp = requests.get(url, params=query_params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"TMDB API request failed for {endpoint}: {e}")
            return None

    def _load_genres(self):
        movie_genres = self._get("/genre/movie/list") or {}
        tv_genres = self._get("/genre/tv/list") or {}
        
        for g in movie_genres.get("genres", []):
            self._genre_map[g["id"]] = g["name"]
        for g in tv_genres.get("genres", []):
            self._genre_map[g["id"]] = g["name"]

    def get_genre_name(self, genre_id: int) -> str:
        return self._genre_map.get(genre_id, "Drama")

    def format_title_data(self, item: Dict[str, Any], media_type: str = "movie") -> Dict[str, Any]:
        """Normalize raw TMDB API response into a standard item dictionary."""
        item_id = item.get("id")
        title = item.get("title") or item.get("name") or "Unknown Title"
        overview = item.get("overview", "No description available.")
        release_date = item.get("release_date") or item.get("first_air_date") or ""
        year = release_date.split("-")[0] if release_date else ""
        vote_avg = item.get("vote_average", 0.0)
        vote_count = item.get("vote_count", 0)
        popularity = item.get("popularity", 0.0)
        
        genre_ids = item.get("genre_ids", [])
        genres = [self.get_genre_name(gid) for gid in genre_ids if gid in self._genre_map]
        if not genres and "genres" in item:
            genres = [g["name"] for g in item["genres"]]
        
        poster_path = item.get("poster_path")
        backdrop_path = item.get("backdrop_path")
        
        poster_url = f"{self.image_base_url}/w500{poster_path}" if poster_path else None
        backdrop_url = f"{self.image_base_url}/original{backdrop_path}" if backdrop_path else None

        return {
            "tmdb_id": item_id,
            "title": title,
            "media_type": media_type,
            "overview": overview,
            "release_date": release_date,
            "year": year,
            "rating": round(vote_avg, 1),
            "vote_count": vote_count,
            "popularity": round(popularity, 1),
            "genres": genres or ["Drama"],
            "poster_url": poster_url,
            "backdrop_url": backdrop_url,
            "director": item.get("director", "N/A"),
            "cast": item.get("cast", [])
        }

    def get_trending(self, media_type: str = "movie", time_window: str = "day") -> List[Dict[str, Any]]:
        res = self._get(f"/trending/{media_type}/{time_window}")
        if not res:
            return self._mock_titles(media_type, "Trending")
        return [self.format_title_data(item, media_type) for item in res.get("results", [])]

    def get_popular(self, media_type: str = "movie") -> List[Dict[str, Any]]:
        res = self._get(f"/{media_type}/popular")
        if not res:
            return self._mock_titles(media_type, "Popular")
        return [self.format_title_data(item, media_type) for item in res.get("results", [])]

    def get_top_rated(self, media_type: str = "movie") -> List[Dict[str, Any]]:
        res = self._get(f"/{media_type}/top_rated")
        if not res:
            return self._mock_titles(media_type, "Top Rated")
        return [self.format_title_data(item, media_type) for item in res.get("results", [])]

    def get_upcoming_or_now_playing(self) -> List[Dict[str, Any]]:
        res_upcoming = self._get("/movie/upcoming") or {}
        res_now = self._get("/movie/now_playing") or {}
        
        results = res_upcoming.get("results", []) + res_now.get("results", [])
        if not results:
            return self._mock_titles("movie", "Upcoming")
        return [self.format_title_data(item, "movie") for item in results]

    def _mock_titles(self, media_type: str, category: str) -> List[Dict[str, Any]]:
        """Return high-quality realistic mock titles when API key is missing or calls fail."""
        mock_data = [
            {
                "tmdb_id": 101,
                "title": "Inception",
                "media_type": "movie",
                "overview": "A thief who steals corporate secrets through dream-sharing technology.",
                "release_date": "2010-07-16",
                "year": "2010",
                "rating": 8.8,
                "vote_count": 35000,
                "popularity": 120.5,
                "genres": ["Sci-Fi", "Action"],
                "poster_url": "https://image.tmdb.org/t/p/w500/oYu2Oh1St1z6Ch9vhx8k2ee9TZ9.jpg",
                "backdrop_url": "https://image.tmdb.org/t/p/original/8ZTVqvKDQ8emSGUEMjsS4yHAiKA.jpg",
                "director": "Christopher Nolan",
                "cast": ["Leonardo DiCaprio"]
            },
            {
                "tmdb_id": 102,
                "title": "Interstellar",
                "media_type": "movie",
                "overview": "A team of explorers travel through a wormhole in space to ensure humanity's survival.",
                "release_date": "2014-11-07",
                "year": "2014",
                "rating": 8.6,
                "vote_count": 32000,
                "popularity": 150.2,
                "genres": ["Sci-Fi", "Drama"],
                "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
                "backdrop_url": "https://image.tmdb.org/t/p/original/pbrkL8cL9vHK3VyVBDMMYfvz2qB.jpg",
                "director": "Christopher Nolan",
                "cast": ["Matthew McConaughey"]
            },
            {
                "tmdb_id": 103,
                "title": "The Dark Knight",
                "media_type": "movie",
                "overview": "When the menace known as the Joker wreaks havoc and chaos on Gotham.",
                "release_date": "2008-07-18",
                "year": "2008",
                "rating": 9.0,
                "vote_count": 31000,
                "popularity": 110.8,
                "genres": ["Action", "Crime"],
                "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
                "backdrop_url": "https://image.tmdb.org/t/p/original/hkBaDkMWbLaf8B1lsWsKX7Ew3Xq.jpg",
                "director": "Christopher Nolan",
                "cast": ["Christian Bale"]
            },
            {
                "tmdb_id": 104,
                "title": "Dune: Part Two",
                "media_type": "movie",
                "overview": "Paul Atreides unites with Chani and the Fremen while seeking revenge.",
                "release_date": "2024-03-01",
                "year": "2024",
                "rating": 8.5,
                "vote_count": 8500,
                "popularity": 220.0,
                "genres": ["Adventure", "Sci-Fi"],
                "poster_url": "https://image.tmdb.org/t/p/w500/1pdfLPoWuVzhAcStTWyFWUtLtfz.jpg",
                "backdrop_url": "https://image.tmdb.org/t/p/original/xOMo8BRK7PfcJv9Z87P0K7v9s8n.jpg",
                "director": "Denis Villeneuve",
                "cast": ["Timothée Chalamet"]
            },
            {
                "tmdb_id": 105,
                "title": "Whiplash",
                "media_type": "movie",
                "overview": "A promising young drummer enlists at a cut-throat music conservatory.",
                "release_date": "2014-10-10",
                "year": "2014",
                "rating": 8.4,
                "vote_count": 14000,
                "popularity": 45.0,
                "genres": ["Drama", "Music"],
                "poster_url": "https://image.tmdb.org/t/p/w500/7fn624j5lj3xTme2SgiLCeMYPhO.jpg",
                "backdrop_url": "https://image.tmdb.org/t/p/original/uV9l42n1Lqf23x9k2vLqW11.jpg",
                "director": "Damien Chazelle",
                "cast": ["Miles Teller"]
            },
            {
                "tmdb_id": 106,
                "title": "Pulp Fiction",
                "media_type": "movie",
                "overview": "The lives of two mob hitmen, a boxer, and a gangster's wife intertwine.",
                "release_date": "1994-10-14",
                "year": "1994",
                "rating": 8.9,
                "vote_count": 27000,
                "popularity": 85.0,
                "genres": ["Crime", "Thriller"],
                "poster_url": "https://image.tmdb.org/t/p/w500/d5NBoStandard.jpg",
                "backdrop_url": "https://image.tmdb.org/t/p/original/suaStandard.jpg",
                "director": "Quentin Tarantino",
                "cast": ["John Travolta"]
            },
            {
                "tmdb_id": 107,
                "title": "The Matrix",
                "media_type": "movie",
                "overview": "A computer hacker learns about the true nature of reality.",
                "release_date": "1999-03-31",
                "year": "1999",
                "rating": 8.7,
                "vote_count": 25000,
                "popularity": 95.0,
                "genres": ["Sci-Fi", "Action"],
                "poster_url": "https://image.tmdb.org/t/p/w500/f89tz.jpg",
                "backdrop_url": "https://image.tmdb.org/t/p/original/n2.jpg",
                "director": "The Wachowskis",
                "cast": ["Keanu Reeves"]
            },
            {
                "tmdb_id": 108,
                "title": "Gladiator",
                "media_type": "movie",
                "overview": "A former Roman General sets out to exact vengeance against the corrupt emperor.",
                "release_date": "2000-05-05",
                "year": "2000",
                "rating": 8.5,
                "vote_count": 18000,
                "popularity": 75.0,
                "genres": ["Action", "Adventure"],
                "poster_url": "https://image.tmdb.org/t/p/w500/ty.jpg",
                "backdrop_url": "https://image.tmdb.org/t/p/original/g1.jpg",
                "director": "Ridley Scott",
                "cast": ["Russell Crowe"]
            },
            {
                "tmdb_id": 109,
                "title": "Fight Club",
                "media_type": "movie",
                "overview": "An insomniac office worker and a devil-may-care soap maker form an underground fight club.",
                "release_date": "1999-10-15",
                "year": "1999",
                "rating": 8.4,
                "vote_count": 28000,
                "popularity": 90.0,
                "genres": ["Drama", "Thriller"],
                "poster_url": "https://image.tmdb.org/t/p/w500/fc.jpg",
                "backdrop_url": "https://image.tmdb.org/t/p/original/fcb.jpg",
                "director": "David Fincher",
                "cast": ["Brad Pitt"]
            },
            {
                "tmdb_id": 110,
                "title": "Se7en",
                "media_type": "movie",
                "overview": "Two detectives hunt a serial killer who uses the seven deadly sins as his motives.",
                "release_date": "1995-09-22",
                "year": "1995",
                "rating": 8.6,
                "vote_count": 21000,
                "popularity": 65.0,
                "genres": ["Crime", "Mystery"],
                "poster_url": "https://image.tmdb.org/t/p/w500/s7.jpg",
                "backdrop_url": "https://image.tmdb.org/t/p/original/s7b.jpg",
                "director": "David Fincher",
                "cast": ["Morgan Freeman"]
            }
        ]
        return mock_data
