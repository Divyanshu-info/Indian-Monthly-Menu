"""Month -> {season, vegetables, fruits} for India.

Sourced from Indian seasonal produce calendars (Rabi/Kharif/Zaid cycles):
- Winter (Rabi harvest): Nov-Feb
- Summer (Zaid): Mar-Jun
- Monsoon (Kharif): Jul-Oct
"""

WINTER_VEG = [
    "Spinach (Palak)", "Fenugreek (Methi)", "Mustard Greens (Sarson)",
    "Cauliflower (Gobi)", "Cabbage (Patta Gobi)", "Green Peas (Matar)",
    "Carrot (Gajar)", "Radish (Mooli)", "Beetroot (Chukandar)", "Broccoli",
]
WINTER_FRUIT = [
    "Orange (Santra)", "Sweet Lime (Mosambi)", "Kinnow", "Guava (Amrud)",
    "Grapes (Angoor)", "Strawberry", "Apple (Seb)", "Custard Apple (Sitaphal)",
]

SUMMER_VEG = [
    "Bottle Gourd (Lauki)", "Ridge Gourd (Turai)", "Bitter Gourd (Karela)",
    "Cucumber (Kheera)", "Okra (Bhindi)", "Pumpkin (Kaddu)",
    "Cluster Beans (Guar)", "Snake Gourd (Chichinda)", "Tinda", "Amaranth (Chaulai)",
]
SUMMER_FRUIT = [
    "Mango (Aam)", "Watermelon (Tarbooj)", "Muskmelon (Kharbooja)",
    "Litchi", "Jackfruit (Kathal)", "Banana (Kela)", "Papaya (Papita)",
]

MONSOON_VEG = [
    "Okra (Bhindi)", "Snake Gourd (Chichinda)", "Taro Root (Arbi)",
    "Yam (Suran)", "Bottle Gourd (Lauki)", "Ridge Gourd (Turai)",
    "Corn (Bhutta)", "Spinach (Palak)", "Green Chilli (Hari Mirch)", "Ginger (Adrak)",
]
MONSOON_FRUIT = [
    "Jamun", "Custard Apple (Sitaphal)", "Pomegranate (Anar)",
    "Pear (Nashpati)", "Plum (Aloo Bukhara)", "Peach (Aaru)",
    "Banana (Kela)", "Papaya (Papita)",
]

SEASONAL: dict[int, dict] = {
    1:  {"season": "Winter",  "vegetables": WINTER_VEG,  "fruits": WINTER_FRUIT},
    2:  {"season": "Winter",  "vegetables": WINTER_VEG,  "fruits": WINTER_FRUIT},
    3:  {"season": "Summer",  "vegetables": SUMMER_VEG,  "fruits": SUMMER_FRUIT},
    4:  {"season": "Summer",  "vegetables": SUMMER_VEG,  "fruits": SUMMER_FRUIT},
    5:  {"season": "Summer",  "vegetables": SUMMER_VEG,  "fruits": SUMMER_FRUIT},
    6:  {"season": "Summer",  "vegetables": SUMMER_VEG,  "fruits": SUMMER_FRUIT},
    7:  {"season": "Monsoon", "vegetables": MONSOON_VEG, "fruits": MONSOON_FRUIT},
    8:  {"season": "Monsoon", "vegetables": MONSOON_VEG, "fruits": MONSOON_FRUIT},
    9:  {"season": "Monsoon", "vegetables": MONSOON_VEG, "fruits": MONSOON_FRUIT},
    10: {"season": "Monsoon", "vegetables": MONSOON_VEG, "fruits": MONSOON_FRUIT},
    11: {"season": "Winter",  "vegetables": WINTER_VEG,  "fruits": WINTER_FRUIT},
    12: {"season": "Winter",  "vegetables": WINTER_VEG,  "fruits": WINTER_FRUIT},
}


def get_season(month: int) -> str:
    return SEASONAL.get(month, {}).get("season", "All")
