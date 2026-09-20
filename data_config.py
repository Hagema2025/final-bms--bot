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
        AGS_CINEMAS_MADURAVOYAL = "AGS Cinemas: Maduravoyal"
        AGS_CINEMAS_OMR_NAVLUR = "AGS Cinemas OMR: Navlur"
        AGS_CINEMAS_T_NAGAR = "AGS Cinemas: T. Nagar"
        AGS_CINEMAS_VILLIVAKKAM = "AGS Cinemas: Villivakkam"
        ANAND_THEATRE_MADHURANTHAGAM_RGB_LASER_4K = "Anand Theatre Madhuranthagam RGB LASER 4k"
        ARUL_MURUGA_THEATRE_4K_THIRUPORUR = "Arul Muruga Theatre 4K: Thiruporur"
        AVM_CINEMAS_UTHUKKOTTAI = "AVM Cinemas: Uthukkottai"
        CINEPOLIS_BSR_MALL_OMR_THORAIPAKKAM = "Cinepolis: BSR Mall, OMR, Thoraipakkam"
        GANAPATHYRAM_THEATRE_4K_DOLBY_7_1_CHENNAI = "GanapathyRam Theatre 4K Dolby 7.1: Chennai"
        GAYATHIRI_CINEMAS_A_C_DOLBY_ATMOS_MADURANTHAKAM = "Gayathiri Cinemas A/C Dolby Atmos: Maduranthakam"
        GK_CINEMAS_RGB_LASER_SRL_4D_PORUR = "GK Cinemas RGB + Laser SRL 4D: Porur"
        GOKULAM_CINEMAS_4K_DOLBY_ATMOS_POONAMALLE = "Gokulam Cinemas 4K Dolby Atmos: Poonamalle"
        GOPALAKRISHNA_A_C_2K_DOLBY_7_1_KARANODAI_REDHILLS = "Gopalakrishna A/C 2K DOLBY 7.1-Karanodai(Redhills)"
        GREEN_CINEMAS_4K_ATMOS_PLF_PADI = "Green Cinemas 4K Atmos, PLF: Padi"
        HDFC_MILLENNIA_PVR_ESCAPE_EXPRESS_AVENUE_MALL = "HDFC Millennia PVR: Escape-Express Avenue Mall"
        INOX_CHENNAI_CITI_CENTRE_DR_RK_SALAI = "INOX: Chennai Citi Centre, Dr. RK Salai"
        INOX_LUXE_PHOENIX_MARKET_CITY_VELACHERY = "INOX: LUXE Phoenix Market City, Velachery"
        INOX_NATIONAL_ARCOT_ROAD = "INOX National: Arcot Road"
        INOX_THE_MARINA_MALL_OMR = "INOX: The Marina Mall, OMR"
        JANATHA_THEATRE_4K_AC_DTS_JBL_AUDIO_PALLAVARAM = "Janatha Theatre 4K AC DTS (JBL AUDIO): Pallavaram"
        JOTHI_THEATRE_4K_A_C_DTS_ST_THOMAS_MOUNT = "Jothi Theatre 4K A/c DTS: ST Thomas Mount"
        KASI_TALKIES_DOLBY_ATMOS_ASHOK_NAGAR = "Kasi Talkies Dolby Atmos: Ashok Nagar"
        KC_KRISHNAVENICINEMAS_RG3_LASER_DOLBYATMOS_TNAGAR = "KC(KrishnaveniCinemas) RG3 LASER DOLBYATMOS TNAGAR"
        KUMARAN_THEATRE_PROVA_4K_DOLBY_ATMOS_MADIPAKKAM = "Kumaran Theatre PROVA 4K DOLBY ATMOS: Madipakkam"
        LATHAA_CINEMAS_A_C_ATMOS_2K_3D_CHENGALPATTU = "Lathaa Cinemas A/C Atmos 2K 3D: Chengalpattu"
        MANI_TALKIES_2K_RGB_LASER_ATMOS_MINJUR = "Mani Talkies 2K RGB Laser ATMOS: Minjur"
        MARVEL_MOVIE_MAX_4K_LASER_DOLBY_ATMOS_TIRUVALLUR = "Marvel Movie Max 4K Laser Dolby Atmos: Tiruvallur"
        MAYAJAAL_MULTIPLEX_ECR_CHENNAI = "MAYAJAAL Multiplex: ECR, Chennai"
        MEDAVAKKAM_KUMARAN_CINEMAS_RGB_LASER_DOLBY_ATMOS = "Medavakkam Kumaran Cinemas RGB LASER Dolby Atmos"
        MEENAKSHI_CINEMAS_RAKKI_4K_DOLBY_ATMOS_AVADI = "Meenakshi Cinemas (Rakki) 4K Dolby Atmos: Avadi"
        MIRAJ_CINEMAS_SEKARAN_MALL_PERRUMBAKKAM = "Miraj Cinemas: Sekaran Mall, Perrumbakkam"
        MOVIEMAX_PR_MALL_WALL_TAX_ROAD_CHENNAI = "MovieMax: PR Mall, Wall Tax Road, Chennai"
        NATIONAL_THEATRE_4K_DOLBY_ATMOS_TAMBARAM = "National Theatre 4K Dolby Atmos: Tambaram"
        ODIYAN_MANI_THEATRE_2K_A_C_DOLBY_THIRUVOTTIYUR = "Odiyan Mani Theatre 2k A/c Dolby: Thiruvottiyur"
        PVR_AEROHUB_CHENNAI = "PVR: Aerohub, Chennai"
        PVR_AMPA_MALL_NELSON_MANICKAM_ROAD = "PVR: Ampa Mall, Nelson Manickam Road"
        PVR_GRAND_GALADA_PALLAVARAM = "PVR: Grand Galada, Pallavaram"
        PVR_GRAND_MALL_VELACHERY = "PVR: Grand Mall, Velachery"
        PVR_HERITAGE_RSL_ECR_CHENNAI = "PVR: Heritage RSL ECR, Chennai"
        PVR_PALAZZO_THE_NEXUS_VIJAYA_MALL = "PVR: Palazzo, The Nexus Vijaya Mall"
        PVR_PERAMBUR_SPECTRUM_MALL = "PVR: Perambur, Spectrum Mall"
        PVR_SATHYAM_ROYAPETTAH = "PVR: Sathyam, Royapettah"
        PVR_SKLS_GALAXY_MALL_RED_HILLS_CHENNAI = "PVR: SKLS Galaxy Mall, Red Hills Chennai"
        PVR_VR_CHENNAI_ANNA_NAGAR = "PVR: VR Chennai, Anna Nagar"
        RAKKI_CINEMAS_OMR_KELAMBAKKAM = "Rakki Cinemas: OMR, Kelambakkam"
        RAKKI_RGB_LASER_4K_THIRUVALLUR = "Rakki RGB Laser 4K: Thiruvallur"
        REMY_CINEMAS_A_C_DTS_2K_3D_LASER_AVADI = "Remy Cinemas A/C DTS 2K 3D Laser: Avadi"
        ROHINI_SILVER_SCREENS_KOYAMBEDU = "Rohini Silver Screens: Koyambedu"
        SB_CINEMAS_SRI_BHAGAVATHI_4K_ATMOS_POONAMALLEE = "SB Cinemas (Sri Bhagavathi) 4K Atmos: Poonamallee"
        SHREE_RADHA_MOVIE_PARK_4K_DOLBY_ATMOS_REDHILLS = "Shree Radha Movie Park 4K Dolby Atmos: Redhills"
        SIVASAKTHI_CINEMAS_RGB_4K_LASER_PADI = "Sivasakthi Cinemas RGB 4K Laser: Padi"
        SLB_LAKSHMIBALA_MOVIE_PARK_4K_DOLBY_ATMOS_PADI = "SLB (LakshmiBala) Movie Park 4K Dolby Atmos: Padi"
        SRI_HARI_THEATRE_DOLBY_ATMOS_PATTABIRAM = "Sri Hari Theatre Dolby Atmos: Pattabiram"
        THE_VIJAY_PARK_MULTIPLEX_INJAMBAKKAM_ECR_4K_ATMOS = "The Vijay Park Multiplex: Injambakkam ECR 4K Atmos"
        VELA_CINEMAS_RGB_4KLASER_DOLBYATMOS_THIRUNINRAVUR = "Vela Cinemas RGB 4KLaser DolbyAtmos: Thiruninravur"
        VELS_THEATRES_CHENNAI = "Vels Theatres: Chennai"
        VENKATESWARA_CINEMAS_DOLBY_ATMOS_KUNDRATHUR = "Venkateswara Cinemas DOLBY ATMOS: Kundrathur"
        VETRIVEL_RGB_DOLBY_NANGANALLUR_NEWLY_RENOVATED = "VETRIVEL RGB DOLBY:NANGANALLUR (NEWLY RENOVATED)"
        VIGNESHWARA_THEATRE_RGB_LASER_POONAMALLEE = "Vigneshwara Theatre RGB Laser: Poonamallee"
        VR_CINEMAS_RGB_4K_LASER_DOLBY_ATMOS_PATTABIRAM = "VR Cinemas RGB 4K LASER DOLBY ATMOS: Pattabiram"
        WOODLANDS_THEATRE_CHENNAI = "Woodlands Theatre: Chennai"

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

# ---------------------------------------------------------
# 6. VENUE CODE TO THEATRE NAME MAP
# ---------------------------------------------------------
VENUE_MAP = {
    "RAKK": "Rakki Cinemas: OMR, Kelambakkam",
    "KVCS": "KC(KrishnaveniCinemas) RG3 LASER DOLBYATMOS TNAGAR",
    "RSSC": "Rohini Silver Screens: Koyambedu",
    "TVHP": "The Vijay Park Multiplex: Injambakkam ECR 4K Atmos",
    "RRGB": "Rakki RGB Laser 4K: Thiruvallur",
    "CBMC": "Cinepolis: BSR Mall, OMR, Thoraipakkam",
    "MCXF": "Meenakshi Cinemas (Rakki) 4K Dolby Atmos: Avadi",
    "MAYJ": "MAYAJAAL Multiplex: ECR, Chennai",
    "AGSM": "AGS Cinemas: Maduravoyal",
    "ACON": "AGS Cinemas OMR: Navlur",
    "VVGT": "Vels Theatres: Chennai",
    "KSTK": "Kasi Talkies Dolby Atmos: Ashok Nagar",
    "MCSK": "Miraj Cinemas: Sekaran Mall, Perrumbakkam",
    "PGMV": "PVR: Grand Mall, Velachery",
    "ACVM": "AGS Cinemas: Villivakkam",
    "INPR": "INOX: LUXE Phoenix Market City, Velachery",
    "PCAN": "PVR: VR Chennai, Anna Nagar",
    "ACTN": "AGS Cinemas: T. Nagar",
    "PABC": "PVR: Aerohub, Chennai",
    "PBRM": "PVR: Perambur, Spectrum Mall",
    "GKCP": "GK Cinemas RGB + Laser SRL 4D: Porur",
    "PVHR": "PVR: Heritage RSL ECR, Chennai",
    "FMCN": "INOX National: Arcot Road",
    "VVTN": "VETRIVEL RGB DOLBY:NANGANALLUR (NEWLY RENOVATED)",
    "PGRA": "PVR: Grand Galada, Pallavaram",
    "INTO": "INOX: The Marina Mall, OMR",
    "SSCC": "Sivasakthi Cinemas RGB 4K Laser: Padi",
    "INCH": "INOX: Chennai Citi Centre, Dr. RK Salai",
    "PVHC": "PVR: Ampa Mall, Nelson Manickam Road",
    "SUTC": "Gokulam Cinemas 4K Dolby Atmos: Poonamalle",
    "PVES": "HDFC Millennia PVR: Escape-Express Avenue Mall",
    "AVMT": "AVM Cinemas: Uthukkottai",
    "SBTR": "SB Cinemas (Sri Bhagavathi) 4K Atmos: Poonamallee",
    "GAHC": "Gopalakrishna A/C 2K DOLBY 7.1-Karanodai(Redhills)",
    "AMTT": "Arul Muruga Theatre 4K: Thiruporur",
    "GCRP": "Green Cinemas 4K Atmos, PLF: Padi",
    "HRSR": "Sri Hari Theatre Dolby Atmos: Pattabiram",
    "GKGM": "Gayathiri Cinemas A/C Dolby Atmos: Maduranthakam",
    "NLTC": "National Theatre 4K Dolby Atmos: Tambaram",
    "ATMG": "Anand Theatre Madhuranthagam RGB LASER 4k",
    "JTPL": "Janatha Theatre 4K AC DTS (JBL AUDIO): Pallavaram",
    "RDMP": "Shree Radha Movie Park 4K Dolby Atmos: Redhills",
    "WSTC": "Woodlands Theatre: Chennai",
    "LKOP": "Lathaa Cinemas A/C Atmos 2K 3D: Chengalpattu",
    "KMRM": "Kumaran Theatre PROVA 4K DOLBY ATMOS: Madipakkam",
    "PVSR": "PVR: Sathyam, Royapettah",
    "PSKL": "PVR: SKLS Galaxy Mall, Red Hills Chennai",
    "MMKC": "Medavakkam Kumaran Cinemas RGB LASER Dolby Atmos",
    "GRTC": "GanapathyRam Theatre 4K Dolby 7.1: Chennai",
    "PVPZ": "PVR: Palazzo, The Nexus Vijaya Mall",
    "SVWT": "Vigneshwara Theatre RGB Laser: Poonamallee",
    "MLMT": "Marvel Movie Max 4K Laser Dolby Atmos: Tiruvallur",
    "MMPR": "MovieMax: PR Mall, Wall Tax Road, Chennai",
    "JOTG": "Jothi Theatre 4K A/c DTS: ST Thomas Mount",
    "VCDK": "Venkateswara Cinemas DOLBY ATMOS: Kundrathur",
    "MTLM": "Mani Talkies 2K RGB Laser ATMOS: Minjur",
    "SLMP": "SLB (LakshmiBala) Movie Park 4K Dolby Atmos: Padi",
    "VECT": "Vela Cinemas RGB 4KLaser DolbyAtmos: Thiruninravur",
    "VRCP": "VR Cinemas RGB 4K LASER DOLBY ATMOS: Pattabiram",
    "REMC": "Remy Cinemas A/C DTS 2K 3D Laser: Avadi",
    "OMTT": "Odiyan Mani Theatre 2k A/c Dolby: Thiruvottiyur",
}
