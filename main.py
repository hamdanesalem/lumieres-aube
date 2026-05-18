import flet as ft
import flet_geolocator as fg
import requests
import math
import json
import os
import tempfile
from datetime import datetime, timedelta

# Utilisation d'un chemin sécurisé pour Android au lieu de la racine en lecture seule
CONFIG_FILE = os.path.join(tempfile.gettempdir(), "lumieres_aube_config.json")

def load_saved_state():
    default_state = {
        "city": "Annaba",
        "country": "Algérie",
        "lat": 36.905,
        "lon": 7.755
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_state
    return default_state

def save_state_to_file(name, country, lat, lon):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"city": name, "country": country, "lat": lat, "lon": lon}, f, ensure_ascii=False, indent=4)
    except:
        pass

def get_suggestions(search_text):
    if len(search_text) < 3:
        return []
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={search_text}&count=4&language=fr"
        r = requests.get(url, timeout=3).json()
        results = r.get("results", [])
        suggestions = []
        for res in results:
            name = res.get("name", "")
            country = res.get("country", "")
            admin = res.get("admin1", "")
            lat = float(res.get("latitude"))
            lon = float(res.get("longitude"))
            
            if country.lower() in ["algeria", "algerie"]:
                country = "Algérie"
                
            label = f"{name} ({admin}), {country}" if admin else f"{name}, {country}"
            suggestions.append({"label": label, "name": name, "country": country, "lat": lat, "lon": lon})
        return suggestions
    except:
        return []

def calc_dawn_time(lat, lon, date, angle):
    day_of_year = date.timetuple().tm_yday
    declination = 0.4093 * math.sin(2 * math.pi * (284 + day_of_year) / 365)
    lat_rad = math.radians(lat)
    angle_rad = math.radians(angle)
    
    try:
        cos_H = (math.sin(angle_rad) - math.sin(lat_rad) * math.sin(declination)) / (math.cos(lat_rad) * math.cos(declination))
        if cos_H > 1 or cos_H < -1:
            return None
        H = math.degrees(math.acos(cos_H))
    except:
        return None

    solar_noon = 12.0 - (lon - 15.0) / 15.0 
    dawn_hours = solar_noon - (H / 15.0)
    
    b = 2 * math.pi * (day_of_year - 81) / 364
    eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    dawn_hours -= (eot / 60.0)

    hour = int(dawn_hours)
    minute = int((dawn_hours - hour) * 60)
    return datetime(date.year, date.month, date.day, hour, minute)

# La vraie logique de l'application isolée pour intercepter les crashs au démarrage
def run_safe_app(page: ft.Page):
    page.title = "Lumières de l'Aube"
    page.window.width = 360
    page.window.height = 690
    page.window.resizable = False
    page.bgcolor = "#1A2639"
    page.theme_mode = ft.ThemeMode.DARK
    page.safe_area = True
    page.padding = ft.Padding.symmetric(horizontal=12, vertical=8)
    page.spacing = 0

    saved = load_saved_state()
    state = {
        "lang": "FR", 
        "city": saved["city"], 
        "country": saved["country"],
        "lat": saved["lat"], 
        "lon": saved["lon"], 
        "date": datetime.now()
    }

    TRAD = {
        "FR": {
            "title": "Lumières de l'Aube", "choose_date": "Choisir une date :",
            "h18": "Fausse Aube (-18°)", "h15": "Fil de Lumière (-15°)", "h12": "Aube Nautique (-12°)",
            "wait": "Attente : + ", "min": " min", "gps": "GPS",
            "f1": "1. -18° : Lumière verticale (Fajr Kadhib).",
            "f2": "2. -15° : Premier trait horizontal net sur la mer.",
            "f3": "3. -12° : L'horizon devient visible et clair.",
            "search_hint": "Rechercher une ville..."
        },
        "ARA": {
            "title": "أضواء الفجر", "choose_date": "اختر التاريخ:",
            "h18": "الفجر الكاذب (-18°)", "h15": "خيط الضوء الأول (-15°)", "h12": "الفجر الملاحي (-12°)",
            "wait": "الانتظار: + ", "min": " دقيقة", "gps": "GPS",
            "f1": "1. -18 درجة: ضوء عمودي (الفجر الكاذب).",
            "f2": "2. -15 درجة: أول خيط أفقي فوق البحر.",
            "f3": "3. -12 درجة: وضوح الأفق تماماً.",
            "search_hint": "ابحث عن مدينة..."
        },
        "EN": {
            "title": "Lights of Dawn", "choose_date": "Choose a date:",
            "h18": "False Dawn (-18°)", "h15": "Thread of Light (-15°)", "h12": "Nautical Dawn (-12°)",
            "wait": "Waiting: + ", "min": " min", "gps": "GPS",
            "f1": "1. -18°: Vertical light (Fajr Kadhib).",
            "f2": "2. -15°: First sharp horizontal line over the sea.",
            "f3": "3. -12°: Horizon becomes clear and visible.",
            "search_hint": "Search city..."
        }
    }

    txt_main_title = ft.Text("", size=22, weight="bold", color="#4A90E2")
    txt_location = ft.Text("", size=13, color="#8F9BB3")
    txt_choose = ft.Text("", size=13, color="white")
    txt_date_display = ft.Text("", size=16, weight="bold", color="white")
    
    btn_gps = ft.FilledButton("", icon=ft.Icons.GPS_FIXED, on_click=lambda e: sync_hardware_gps(e))
    timeline_container = ft.Column(spacing=8)
    
    footer_text1 = ft.Text("", size=11, color="#8F9BB3")
    footer_text2 = ft.Text("", size=11, color="#8F9BB3")
    footer_text3 = ft.Text("", size=11, color="#8F9BB3")

    lang_dropdown = ft.Dropdown(
        width=150,
        text_size=12,
        color="white",
        filled=True,
        fill_color="#161F30",
        border_color="#314563",
        value=state["lang"],
        options=[
            ft.DropdownOption(key="FR", text="🇫🇷 Français"),
            ft.DropdownOption(key="ARA", text="🇩🇿 العربية"),
            ft.DropdownOption(key="EN", text="🇬🇧 English"),
        ],
        on_select=lambda e: set_lang(e.control.value)
    )

    suggestions_container = ft.Column(spacing=2, visible=False)

    def select_suggestion(data):
        state.update({
            "city": data["name"],
            "country": data["country"],
            "lat": data["lat"],
            "lon": data["lon"]
        })
        save_state_to_file(data["name"], data["country"], data["lat"], data["lon"])
        
        input_search.value = ""
        suggestions_container.controls.clear()
        suggestions_container.visible = False
        update_ui()

    def on_search_change(e):
        val = e.control.value.strip()
        if len(val) < 3:
            suggestions_container.controls.clear()
            suggestions_container.visible = False
            page.update()
            return
            
        suggs = get_suggestions(val)
        suggestions_container.controls.clear()
        
        if len(suggs) > 0:
            suggestions_container.visible = True
            for s in suggs:
                suggestions_container.controls.append(
                    ft.Container(
                        content=ft.Text(s["label"], size=12, color="white"),
                        padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                        bgcolor="#232D3B",
                        border_radius=4,
                        on_click=lambda _, data=s: select_suggestion(data),
                    )
                )
        else:
            suggestions_container.visible = False
            
        page.update()

    input_search = ft.TextField(
        height=44,
        text_size=12,
        color="white",
        content_padding=ft.Padding.only(left=10, right=10),
        on_change=on_search_change,
    )

    def build_timeline_item(title, time_str, wait_str, is_first=False):
        return ft.Row([
            ft.Container(width=4, height=50, bgcolor="#4A90E2" if not is_first else "transparent"),
            ft.Container(width=10, height=10, border_radius=5, bgcolor="#4A90E2"),
            ft.Column([
                ft.Text(title, size=12, color="#8F9BB3"),
                ft.Text(time_str, size=20, weight="bold", color="white"),
                ft.Text(wait_str, size=11, color="#FF6B4A", weight="bold") if wait_str else ft.Container()
            ], spacing=1)
        ], alignment="start")

    def update_ui():
        L = TRAD[state["lang"]]

        lang_dropdown.value = state["lang"]
        input_search.hint_text = L["search_hint"]
        txt_main_title.value = L["title"]
        txt_location.value = f"{state['city']}, {state['country']}"
        
        txt_choose.value = L["choose_date"]
        txt_date_display.value = state["date"].strftime("%d / %m / %Y")
        btn_gps.text = L["gps"]
        
        footer_text1.value = L["f1"]
        footer_text2.value = L["f2"]
        footer_text3.value = L["f3"]

        dt18 = calc_dawn_time(state["lat"], state["lon"], state["date"], -18.0)
        dt15 = calc_dawn_time(state["lat"], state["lon"], state["date"], -15.0)
        dt12 = calc_dawn_time(state["lat"], state["lon"], state["date"], -12.0)

        t18_str = dt18.strftime("%H:%M") if dt18 else "--:--"
        t15_str = dt12_str = ""
        wait_15 = wait_12 = ""

        if dt18 and dt15:
            t15_str = dt15.strftime("%H:%M")
            diff15 = int((dt15 - dt18).total_seconds() / 60)
            wait_15 = f"{L['wait']}{diff15}{L['min']}"

        if dt15 and dt12:
            dt12_str = dt12.strftime("%H:%M")
            diff12 = int((dt12 - dt15).total_seconds() / 60)
            wait_12 = f"{L['wait']}{diff12}{L['min']}"

        timeline_container.controls.clear()
        timeline_container.controls.extend([
            build_timeline_item(L["h18"], t18_str, "", is_first=True),
            build_timeline_item(L["h15"], t15_str, wait_15),
            build_timeline_item(L["h12"], dt12_str, wait_12)
        ])
        page.update()

    def set_lang(lang_code):
        if lang_code:
            state["lang"] = lang_code
            update_ui()

    def change_day(delta):
        state["date"] += timedelta(days=delta)
        update_ui()

    def sync_hardware_gps(e):
        txt_location.value = "[ Recherche signal GPS... ]" if state["lang"] != "ARA" else "[ جاري البحث عن الإشارة... ]"
        page.update()

        try:
            loc = page.platform_location
            if loc and loc.latitude and loc.longitude:
                state.update({
                    "city": "Position GPS",
                    "country": f"({loc.latitude:.2f}N, {loc.longitude:.2f}E)",
                    "lat": float(loc.latitude),
                    "lon": float(loc.longitude)
                })
                save_state_to_file(state["city"], state["country"], float(loc.latitude), float(loc.longitude))
                update_ui()
                return
        except:
            pass

        txt_location.value = f"{state['city']}, {state['country']} (GPS indisponible)"
        page.update()

    header_section = ft.Column(
        [
            ft.Row(
                [lang_dropdown, btn_gps],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Column([
                input_search,
                suggestions_container
            ], spacing=4),
            
            ft.Container(
                content=ft.Column(
                    [txt_main_title, txt_location],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                margin=ft.Margin.only(top=10, bottom=5)
            ),
        ],
        spacing=5,
    )

    timeline_panel = ft.Container(
        content=ft.Column(
            [
                txt_choose,
                ft.Row(
                    [
                        ft.IconButton(
                            ft.Icons.KEYBOARD_ARROW_LEFT,
                            on_click=lambda _: change_day(-1),
                            icon_color="#4A90E2",
                        ),
                        txt_date_display,
                        ft.IconButton(
                            ft.Icons.KEYBOARD_ARROW_RIGHT,
                            on_click=lambda _: change_day(1),
                            icon_color="#4A90E2",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                ft.Divider(height=8, color="#232D3B"),
                timeline_container,
            ],
            spacing=10,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=16,
        bgcolor="#161F30",
        border_radius=12,
        expand=True,
    )

    footer_section = ft.Container(
        content=ft.Column([footer_text1, footer_text2, footer_text3], spacing=4),
        padding=12,
        bgcolor="#0E1624",
        border_radius=10,
    )

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Column(
                [header_section, timeline_panel, footer_section],
                expand=True,
                spacing=10,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )
    )
    update_ui()

# Gestionnaire principal avec filet de sécurité anti-crash
def main(page: ft.Page):
    try:
        run_safe_app(page)
    except Exception as error:
        # Si ça plante au démarrage sur Android, l'erreur s'affichera à l'écran au lieu de fermer l'app
        page.bgcolor = "white"
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("ERREUR DE DEMARRAGE :", color="red", weight="bold", size=16),
                    ft.Text(str(error), color="black", size=14)
                ]),
                padding=20
            )
        )
        page.update()

if __name__ == "__main__":
    ft.run(main)

