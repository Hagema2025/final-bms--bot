# data_config.py

# ---------------------------------------------------------
# 1. CITIES
# ---------------------------------------------------------
class Cities:
    CHENNAI = {"name": "Chennai", "code": "CHEN", "slug": "chennai"}
    MADURAI = {"name": "Madurai", "code": "MADU", "slug": "madurai"}

    @classmethod
    def get_all_cities(cls):
        return [cls.CHENNAI, cls.MADURAI]


# ---------------------------------------------------------
# 2. THEATRES
# ---------------------------------------------------------
class Theatres:
    class Chennai:
        AGS_NAVALUR = "AGS Cinemas OMR: Navlur"
        AGS_MADURAVOYAL = "AGS Cinemas: Maduravoyal"
        AGS_TNAGAR = ""
        AGS_VILLIVAKKAM = "AGS Cinemas: Villivakkam"
        PVR_PALAZZO = ""
        PVR_SATHYAM = "PVR: Sathyam, Royapettah"
        PVR_VR = ""
        PVR_GRAND_MALL = "PVR: Grand Mall, Velachery"
        PVR_GRAND_GALADA = "PVR: Grand Galada, Pallavaram"
        PVR_AEROHUB = "PVR: Aerohub, Chennai"
        PVR_HERITAGE = "PVR: Heritage RSL ECR, Chennai"
        PVR_SPECTRUM = "PVR: Perambur, Spectrum Mall"
        PVR_AMPA = "PVR: Ampa Mall, Nelson Manickam Road"
        PVR_ESCAPE = "HDFC Millennia PVR: Escape-Express Avenue Mall"
        INOX_LUXE = ""
        INOX_NATIONAL = ""
        INOX_MARINA = "INOX: The Marina Mall, OMR"
        INOX_CITI_CENTRE = ""
        CINEPOLIS_BSR = "Cinepolis: BSR Mall, OMR, Thoraipakkam"
        ROHINI = ""
        MAYAJAAL = "MAYAJAAL Multiplex: ECR, Chennai"
        RAKKI_OMR = "Rakki Cinemas: OMR, Kelambakkam"
        MIRAJ_SEKARAN = "Miraj Cinemas: Sekaran Mall, Perrumbakkam"

    class Madurai:
        VETRI_MATTUTHAVANI = "Vetri Cinemas (Maattuthavani) Dolby Atmos: Madurai"


    @classmethod
    def get_all(cls):
        """Fallback if city is not found"""
        all_t = []
        all_t.extend([v for k, v in vars(cls.Chennai).items() if not k.startswith("_")])
        all_t.extend([v for k, v in vars(cls.Madurai).items() if not k.startswith("_")])
        return all_t

    @classmethod
    def get_by_city(cls, city_slug):
        if city_slug == "chennai":
            return [v for k, v in vars(cls.Chennai).items() if not k.startswith("_")]
        elif city_slug == "madurai":
            return [v for k, v in vars(cls.Madurai).items() if not k.startswith("_")]
        return []


# ---------------------------------------------------------
# 3. LANGUAGES
# ---------------------------------------------------------
class Languages:
    TAMIL = "Tamil"
    MALAYALAM = "Malayalam"
    TELUGU = "Telugu"
    HINDI = "Hindi"
    ENGLISH = "English"
    KANNADA = "Kannada"

    @classmethod
    def get_all(cls):
        return [v for k, v in vars(cls).items() if not k.startswith("_") and isinstance(v, str)]


# ---------------------------------------------------------
# 4. PURE FORMATS (No Languages Attached!)
# ---------------------------------------------------------
class Formats:
    F_2D = "2D"
    F_3D = "3D"
    IMAX_2D = "IMAX 2D"
    IMAX_3D = "IMAX 3D"
    EPIQ = "EPIQ"
    FOUR_DX = "4DX"
    FOUR_DX_3D = "4DX 3D"
    SCREENX = "ScreenX"

    @classmethod
    def get_all(cls):
        return [v for k, v in vars(cls).items() if not k.startswith("_") and isinstance(v, str)]


# ---------------------------------------------------------
# 5. TIME PERIODS
# ---------------------------------------------------------
class TimePeriods:
    MIDNIGHT = "midnight"
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"

    @classmethod
    def get_all(cls):
        return [
            (cls.MIDNIGHT, "🌙 Midnight (12 AM - 6 AM)"),
            (cls.MORNING, "🌅 Morning (6 AM - 12 PM)"),
            (cls.AFTERNOON, "☀️ Afternoon (12 PM - 4 PM)"),
            (cls.EVENING, "🌆 Evening (4 PM - 7 PM)"),
            (cls.NIGHT, "🌃 Night (7 PM - 12 AM)"),
        ]
