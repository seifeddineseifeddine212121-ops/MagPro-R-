from bidi.algorithm import get_display
from datetime import datetime, timedelta
from functools import partial
from kivy.animation import Animation
from kivy.clock import Clock, mainthread
from kivy.config import Config
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.network.urlrequest import UrlRequest
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, ListProperty, BooleanProperty
from kivy.resources import resource_find
from kivy.storage.jsonstore import JsonStore
from kivy.uix.image import AsyncImage, Image
from kivy.uix.modalview import ModalView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFillRoundFlatButton, MDFlatButton, MDFillRoundFlatIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
import arabic_reshaper
import hashlib
import json
import logging
import math
import os
import random
import re
import socket
import sys
import threading
import time
import urllib.parse
import urllib.request
# ==========================================
os.environ['KIVY_NO_CONSOLELOG'] = '1'
os.environ['KIVY_LOG_LEVEL'] = 'error'
Config.set('kivy', 'log_level', 'error')
Config.write()
try:
    import websocket
except ImportError:
    websocket = None
# ==========================================
app_dir = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(app_dir, 'font.ttf')
custom_font_loaded = False
try:
    if os.path.exists(FONT_FILE) and os.path.isfile(FONT_FILE):
        LabelBase.register(name='ArabicFont', fn_regular=FONT_FILE, fn_bold=FONT_FILE)
        LabelBase.register(name='Roboto', fn_regular=FONT_FILE, fn_bold=FONT_FILE)
        LabelBase.register(name='RobotoMedium', fn_regular=FONT_FILE, fn_bold=FONT_FILE)
        LabelBase.register(name='RobotoBold', fn_regular=FONT_FILE, fn_bold=FONT_FILE)
        custom_font_loaded = True
        print('[INFO] Custom font loaded successfully.')
    else:
        print('[WARNING] Custom font file (font.ttf) NOT found. Trying System Arial...')
        import platform
        if platform.system() == 'Windows':
            sys_font = 'C:\\Windows\\Fonts\\arial.ttf'
            if os.path.exists(sys_font):
                LabelBase.register(name='ArabicFont', fn_regular=sys_font, fn_bold=sys_font)
            else:
                raise Exception('System Arial not found')
        else:
            raise Exception('Not Windows system')
except Exception as e:
    print(f'[WARNING] Could not load specific font ({e}). Using Kivy Default.')
    try:
        LabelBase.register(name='ArabicFont', fn_regular='Roboto')
    except:
        pass
# ==========================================
reshaper = arabic_reshaper.ArabicReshaper(configuration={'delete_harakat': True, 'support_ligatures': False, 'use_unshaped_instead_of_isolated': True})
# ==========================================
DEFAULT_PORT = '5000'
# ==========================================
KV_BUILDER = '\n<ProductRecycleItem>:\n    orientation: \'vertical\'\n    size_hint_y: None\n    height: dp(220)\n    padding: 0\n    spacing: 0\n    radius: [16]\n    elevation: 3\n    ripple_behavior: True\n    on_release: root.on_tap()\n    md_bg_color: (1, 1, 1, 1)\n\n    MDRelativeLayout:\n        size_hint_y: 0.75\n        \n        FitImage:\n            source: root.image_source\n            radius: [16, 16, 0, 0]\n            size_hint: (1, 1)\n            pos_hint: {\'center_x\': 0.5, \'center_y\': 0.5}\n            opacity: 1 if root.image_source else 0\n        \n        MDIcon:\n            icon: "food"\n            theme_text_color: "Custom"\n            text_color: (0.8, 0.8, 0.8, 1)\n            font_size: "60sp"\n            pos_hint: {\'center_x\': .5, \'center_y\': .5}\n            opacity: 0 if root.image_source else 1\n            \n    MDBoxLayout:\n        orientation: \'vertical\'\n        size_hint_y: 0.25\n        padding: dp(5)\n        \n        MDLabel:\n            text: root.text_name\n            halign: \'center\'\n            bold: True\n            font_style: "Subtitle1"\n            theme_text_color: "Primary"\n            size_hint_y: 0.6\n            text_size: self.width, None\n            max_lines: 2\n            shorten: False\n            font_name: \'ArabicFont\'\n\n        MDLabel:\n            text: root.text_price\n            halign: \'center\'\n            theme_text_color: "Custom"\n            text_color: (0, 0.7, 0, 1)\n            font_style: "Body2"\n            bold: True\n            size_hint_y: 0.4\n            font_name: \'ArabicFont\'\n\n<ProductRecycleView>:\n    viewclass: \'ProductRecycleItem\'\n    RecycleGridLayout:\n        cols: 2\n        default_size: None, dp(230)\n        default_size_hint: 1, None\n        size_hint_y: None\n        height: self.minimum_height\n        spacing: dp(10)\n        padding: dp(10)\n'
# ==========================================
class NoMenuTextField(MDTextField):

    def _show_cut_copy_paste(self, pos, selection, mode=None):
        pass

    def on_double_tap(self):
        pass

class SmartTextField(MDTextField):

    def __init__(self, **kwargs):
        self._raw_text = kwargs.get('text', '')
        self.base_direction = 'ltr'
        self.halign = 'left'
        self._input_reshaper = arabic_reshaper.ArabicReshaper(configuration={'delete_harakat': True, 'support_ligatures': False, 'use_unshaped_instead_of_isolated': True})
        super().__init__(**kwargs)
        self.font_name = 'ArabicFont'
        self.font_name_hint_text = 'ArabicFont'
        if self._raw_text:
            self._update_display()
        from kivy.core.window import Window
        Window.enable_v_sync = True

    def insert_text(self, substring, from_undo=False):
        self._raw_text += substring
        self._update_display()

    def do_backspace(self, from_undo=False, mode='bkspc'):
        if not self._raw_text:
            return
        self._raw_text = self._raw_text[:-1]
        self._update_display()

    def _update_display(self):
        reshaped = self._input_reshaper.reshape(self._raw_text)
        bidi_text = get_display(reshaped)
        self.text = bidi_text
        self._update_alignment(self._raw_text)

    def _update_alignment(self, text):
        if not text:
            self.halign = 'left'
            self.base_direction = 'ltr'
            return
        has_arabic = any(('\u0600' <= c <= 'ۿ' for c in text))
        if has_arabic:
            self.halign = 'right'
            self.base_direction = 'rtl'
        else:
            self.halign = 'left'
            self.base_direction = 'ltr'

    def get_value(self):
        if not self._raw_text and self.text:
            return self.text
        return self._raw_text

    def clear(self):
        self._raw_text = ''
        self.text = ''
        self._update_alignment('')
        self.halign = 'left'

    def on_text(self, instance, value):
        if not value:
            self._raw_text = ''
            self._update_alignment('')

class ProductRecycleItem(RecycleDataViewBehavior, MDCard):
    index = None
    text_name = StringProperty('')
    text_price = StringProperty('')
    image_source = StringProperty('')
    product_data = ObjectProperty(None)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.text_name = data.get('name_display', '')
        self.text_price = data.get('price_display', '')
        self.image_source = data.get('image_url', '')
        self.product_data = data.get('raw_data')
        return super().refresh_view_attrs(rv, index, data)

    def on_tap(self):
        app = MDApp.get_running_app()
        if self.product_data:
            app.open_add_note_dialog(self.product_data)

class ProductRecycleView(RecycleView):

    def __init__(self, **kwargs):
        super(ProductRecycleView, self).__init__(**kwargs)
        self.data = []

    def on_scroll_y(self, instance, value):
        if value <= 0.05:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'load_more_products'):
                app.load_more_products()

class DataValidator:

    @staticmethod
    def validate_ip(ip_address):
        if not ip_address or not isinstance(ip_address, str):
            return False
        pattern = '^(\\d{1,3}\\.){3}\\d{1,3}$'
        if not re.match(pattern, ip_address):
            return False
        return True

    @staticmethod
    def validate_quantity(qty_text):
        try:
            qty = float(qty_text)
            if qty <= 0:
                raise ValueError('La quantité doit être positive.')
            return qty
        except (ValueError, TypeError):
            raise ValueError('Veuillez saisir une quantité valide.')

    @staticmethod
    def sanitize_note(note_text):
        if not note_text:
            return ''
        return str(note_text).replace('"', '').replace("'", '').strip()[:200]

class WebSocketManager:

    def __init__(self, server_ip, port, on_message_callback, on_connect_callback=None, on_disconnect_callback=None):
        self.server_ip = server_ip
        self.port = port
        self.on_message_callback = on_message_callback
        self.on_connect_callback = on_connect_callback
        self.on_disconnect_callback = on_disconnect_callback
        self.ws = None
        self.connected = False
        self.thread = None
        self.should_reconnect = True
        self.reconnect_delay = 5

    def connect(self):
        if websocket is None:
            logging.warning('Module Websocket manquant.')
            return False

        def _run():
            ws_url = f'ws://{self.server_ip}:{self.port}/ws'
            while self.should_reconnect:
                try:
                    self.ws = websocket.WebSocketApp(ws_url, on_open=self._on_open, on_message=self._on_message, on_error=self._on_error, on_close=self._on_close)
                    self.ws.run_forever(ping_interval=10, ping_timeout=5)
                    if self.should_reconnect:
                        threading.Event().wait(self.reconnect_delay)
                except Exception as e:
                    logging.error(f'WS Connection error: {e}')
                    if self.should_reconnect:
                        threading.Event().wait(self.reconnect_delay)
        self.thread = threading.Thread(target=_run, daemon=True)
        self.thread.start()
        return True

    def _on_open(self, ws):
        self.connected = True
        logging.info('WS Connected')
        if self.on_connect_callback:
            Clock.schedule_once(lambda dt: self.on_connect_callback(), 0)

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            if self.on_message_callback:
                Clock.schedule_once(lambda dt: self.on_message_callback(data), 0)
        except Exception as e:
            logging.error(f'WS Message Error: {e}')

    def _on_error(self, ws, error):
        logging.error(f'WS Error: {error}')
        self.connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        logging.info('WS Closed')
        if self.on_disconnect_callback:
            Clock.schedule_once(lambda dt: self.on_disconnect_callback(), 0)

    def disconnect(self):
        self.should_reconnect = False
        self.connected = False
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        self.ws = None

class ImageCacheManager:

    def __init__(self, base_dir, cache_dir_name='image_cache'):
        self.cache_dir = os.path.join(base_dir, cache_dir_name)
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_cache_path(self, url):
        try:
            filename_part = url.split('/')[-1].split('?')[0]
            url_hash = hashlib.md5(filename_part.encode()).hexdigest()
            extension = os.path.splitext(filename_part)[1]
            if not extension or len(extension) > 5:
                extension = '.jpg'
            filename = f'{url_hash}{extension}'
            return os.path.join(self.cache_dir, filename)
        except Exception:
            return None

    def is_cached(self, url):
        path = self.get_cache_path(url)
        return path and os.path.exists(path)

class CartItemCard(MDCard):

    def __init__(self, item, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.item = item
        self.app = app_ref
        self.orientation = 'horizontal'
        self.padding = dp(8)
        self.spacing = dp(10)
        self.size_hint_y = None
        self.height = dp(100)
        self.radius = [15]
        self.elevation = 1
        icon_box = MDBoxLayout(size_hint_x=None, width=dp(50), pos_hint={'center_y': 0.5})
        icon = MDIcon(icon='food-variant', font_size='32sp', theme_text_color='Custom', text_color=self.app.theme_cls.primary_color, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        icon_box.add_widget(icon)
        self.add_widget(icon_box)
        details_box = MDBoxLayout(orientation='vertical', size_hint_x=0.5, pos_hint={'center_y': 0.5}, spacing=dp(0))
        raw_name = item['name']
        name_text = self.app.fix_text(raw_name)
        is_name_arabic = any(('\u0600' <= c <= 'ۿ' for c in raw_name))
        name_align = 'right' if is_name_arabic else 'left'
        name_lbl = MDLabel(text=name_text, halign=name_align, valign='center', bold=True, font_style='Subtitle2', theme_text_color='Primary', size_hint_y=None, height=dp(40), shorten=False, max_lines=2, font_name='ArabicFont')
        name_lbl.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
        details_box.add_widget(name_lbl)
        note_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20), spacing=dp(5))
        raw_note = item.get('note', '') or '---'
        note_text = self.app.fix_text(raw_note)
        is_note_arabic = any(('\u0600' <= c <= 'ۿ' for c in raw_note))
        note_align = 'right' if is_note_arabic else 'left'
        note_lbl = MDLabel(text=note_text, halign=note_align, font_style='Caption', theme_text_color='Hint', size_hint_x=0.8, shorten=True, font_name='ArabicFont')
        edit_note_btn = MDIconButton(icon='pencil-outline', icon_size='18sp', theme_text_color='Custom', text_color=self.app.theme_cls.primary_color, size_hint=(None, None), size=(dp(24), dp(24)), pos_hint={'center_y': 0.5}, on_release=lambda x: self.app.open_edit_note_dialog(self.item))
        note_box.add_widget(note_lbl)
        note_box.add_widget(edit_note_btn)
        details_box.add_widget(note_box)
        try:
            price_val = int(float(item['price']))
        except:
            price_val = 0
        price_lbl = MDLabel(text=f'{price_val} DA', bold=True, theme_text_color='Custom', text_color=(0, 0.6, 0, 1), font_style='Caption', size_hint_y=None, height=dp(20))
        details_box.add_widget(price_lbl)
        self.add_widget(details_box)
        actions_box = MDBoxLayout(size_hint_x=None, width=dp(110), pos_hint={'center_y': 0.5})
        qty_card = MDCard(size_hint=(None, None), size=(dp(105), dp(40)), radius=[12], md_bg_color=(0.95, 0.95, 0.95, 1), elevation=0, pos_hint={'center_y': 0.5})
        qty_layout = MDBoxLayout(orientation='horizontal', spacing=0, padding=0)
        btn_minus = MDIconButton(icon='minus', icon_size='16sp', theme_text_color='Custom', text_color=(0.9, 0.1, 0.1, 1), on_release=self.decrease_qty, pos_hint={'center_y': 0.5})
        self.lbl_qty = MDLabel(text=str(int(item['qty'])), halign='center', bold=True, font_style='Subtitle1', theme_text_color='Primary', pos_hint={'center_y': 0.5})
        btn_plus = MDIconButton(icon='plus', icon_size='16sp', theme_text_color='Custom', text_color=(0.1, 0.7, 0.2, 1), on_release=self.increase_qty, pos_hint={'center_y': 0.5})
        qty_layout.add_widget(btn_minus)
        qty_layout.add_widget(self.lbl_qty)
        qty_layout.add_widget(btn_plus)
        qty_card.add_widget(qty_layout)
        actions_box.add_widget(qty_card)
        self.add_widget(actions_box)

    def increase_qty(self, x):
        self.item['qty'] += 1
        self.lbl_qty.text = str(int(self.item['qty']))
        self.app.update_cart_totals_live()

    def decrease_qty(self, x):
        if self.item['qty'] > 1:
            self.item['qty'] -= 1
            self.lbl_qty.text = str(int(self.item['qty']))
            self.app.update_cart_totals_live()
        else:
            self.app.remove_from_cart(self.item)

class TableCard(MDCard):

    def __init__(self, table, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.table = table
        self.app = app_ref
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(140)
        self.radius = [12]
        self.elevation = 2
        self.ripple_behavior = True
        self._long_press_event = None
        self._long_press_triggered = False
        self.header_box = MDBoxLayout(size_hint_y=None, height=dp(35), padding=[5, 0], md_bg_color=(0, 0, 0, 0.1))
        table_name = self.app.fix_text(table['name'])
        self.lbl_name = MDLabel(text=table_name, halign='center', bold=True, theme_text_color='Custom', font_name='ArabicFont')
        self.header_box.add_widget(self.lbl_name)
        self.add_widget(self.header_box)
        self.body_box = MDBoxLayout(orientation='vertical', padding=10, spacing=5)
        self.add_widget(self.body_box)
        self.update_state(table)

    def update_state(self, table):
        self.table = table
        status = table['status']
        occupied_seats = table.get('occupied_seats', []) or []
        if status == 'occupied':
            self.md_bg_color = (0.85, 0.3, 0.3, 1)
            if 0 not in occupied_seats and occupied_seats:
                self.md_bg_color = (0.95, 0.95, 0.95, 1)
        elif status == 'reserved':
            self.md_bg_color = (1, 0.6, 0, 1)
        else:
            self.md_bg_color = (0.3, 0.7, 0.3, 1)
        text_color = (1, 1, 1, 1) if self.md_bg_color[0] != 0.95 else (0.2, 0.2, 0.2, 1)
        self.lbl_name.text_color = text_color
        self.body_box.clear_widgets()
        if status == 'occupied' and 0 not in occupied_seats and occupied_seats:
            try:
                chair_count = int(table.get('chairs', 4))
            except:
                chair_count = 4
            grid = MDGridLayout(cols=2, spacing=dp(5), padding=dp(5))
            for i in range(1, chair_count + 1):
                is_busy = i in occupied_seats
                seat_color = (0.85, 0.3, 0.3, 1) if is_busy else (0.3, 0.7, 0.3, 1)
                seat_card = MDCard(md_bg_color=seat_color, radius=[4], elevation=0, ripple_behavior=True)
                seat_card.bind(on_release=lambda x, s=i: self.on_sub_seat_click(s))
                seat_card.add_widget(MDLabel(text=str(i), halign='center', theme_text_color='Custom', text_color=(1, 1, 1, 1), bold=True))
                grid.add_widget(seat_card)
            self.body_box.add_widget(grid)
        else:
            icon_name = 'table-furniture'
            if status == 'occupied':
                icon_name = 'silverware-fork-knife'
            elif status == 'reserved':
                icon_name = 'clock-outline'
            icon = MDIcon(icon=icon_name, theme_text_color='Custom', text_color=text_color, pos_hint={'center_x': 0.5}, font_size='40sp')
            info_text = 'Libre'
            if status == 'occupied':
                try:
                    info_text = f"{int(float(table.get('total', 0)))} DA"
                except:
                    info_text = '0 DA'
            elif status == 'reserved':
                info_text = 'Réservé'
            self.body_box.add_widget(icon)
            self.body_box.add_widget(MDLabel(text=info_text, halign='center', bold=True, theme_text_color='Custom', text_color=text_color, font_style='H6'))

    def on_sub_seat_click(self, seat_num):
        if self.app.move_mode:
            self.app.process_destination_selection(self.table)
        else:
            self.app.current_table = self.table
            self.app.open_seat_order(seat_num)

    def on_press(self):
        self._long_press_triggered = False
        self._long_press_event = Clock.schedule_once(self._on_long_press, 0.8)
        return super().on_press()

    def _on_long_press(self, dt):
        self._long_press_triggered = True
        self.app.initiate_move(self.table)

    def on_release(self):
        if self._long_press_event:
            Clock.unschedule(self._long_press_event)
            self._long_press_event = None
        if not self._long_press_triggered:
            self._handle_normal_tap()
        self._long_press_triggered = False
        return super().on_release()

    def _handle_normal_tap(self):
        if self.app.move_mode:
            self.app.process_destination_selection(self.table)
        else:
            self.app.current_table = self.table
            occupied_seats = self.table.get('occupied_seats', []) or []
            if self.table['status'] == 'occupied' and 0 in occupied_seats:
                self.app.open_seat_order(0)
            else:
                self.app.show_chairs_dialog(self.table)

class RestaurantApp(MDApp):
    cart = []
    all_products = []
    current_table = None
    current_seat = 0
    server_ip = '192.168.1.100'
    local_server_ip = '192.168.1.100'
    external_server_ip = ''
    active_server_ip = '192.168.1.100'
    is_server_reachable = False
    last_ping_ms = 0
    stop_heartbeat = False
    current_user_name = 'ADMIN'
    refresh_event = None
    REFRESH_RATE = 5
    auth_token = None
    token_expiry = None
    TOKEN_LIFETIME = 480
    displayed_products_count = 0
    PRODUCTS_PER_PAGE = 50
    current_product_list_source = []
    is_loading_more = False
    _search_event = None
    ws_manager = None
    image_cache = None
    table_widgets = {}
    request_pending = False
    move_mode = False
    move_source_data = None
    offline_store = None
    cache_store = None
    is_offline_mode = False
    dialog_chairs = None
    dialog_ip = None
    dialog_cart = None
    dialog_note = None
    dialog_edit_note = None
    dialog_move_select = None
    dialog_empty_options = None
    dialog_pending = None
    pending_list_container = None
    status_bar_box = None
    status_bar_label = None
    status_bar_timer = None
    btn_cart = None
    btn_reminder = None
    cart_area = None
    data_dir = ''
    rv_products = None

    def fix_text(self, text):
        if not text:
            return ''
        try:
            text = str(text)
            reshaped_text = reshaper.reshape(text)
            bidi_text = get_display(reshaped_text, base_dir='R')
            return bidi_text
        except:
            return str(text)

    def get_device_id(self):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                content_resolver = PythonActivity.mActivity.getContentResolver()
                Secure = autoclass('android.provider.Settings$Secure')
                android_id = Secure.getString(content_resolver, Secure.ANDROID_ID)
                return str(android_id) if android_id else 'ANDROID_UNKNOWN'
            except Exception as e:
                return 'ANDROID_ERR_ID'
        elif platform == 'win':
            return 'PC_DEBUG_ID_12345'
        return 'UNKNOWN_DEVICE_ID'

    def check_license_validity(self):
        try:
            if not self.store.exists('license'):
                return False
            data = self.store.get('license')
            stored_key = data.get('activ_key')
            if not stored_key:
                return False
            device_id = self.get_device_id()
            salt = f'magpro_resto_mobile_v6_{device_id}_secure_key'
            expected_key = hashlib.sha256(salt.encode()).hexdigest()
            is_valid = stored_key == expected_key
            return is_valid
        except Exception as e:
            return False

    def validate_activation(self, key_input, dialog_ref):
        try:
            device_id = self.get_device_id()
            salt = f'magpro_resto_mobile_v6_{device_id}_secure_key'
            expected_key = hashlib.sha256(salt.encode()).hexdigest()
            if key_input.strip() == expected_key:
                self.store.put('license', activ_key=expected_key)
                self.notify('Activation réussie ! Bienvenue.', 'success')
                if dialog_ref:
                    dialog_ref.dismiss()
                Clock.schedule_once(self._deferred_start, 0.5)
            else:
                self.notify('Clé invalide. Veuillez vérifier.', 'error')
        except Exception as e:
            pass

    def show_activation_dialog(self):
        device_id = self.get_device_id()
        content = MDBoxLayout(orientation='vertical', spacing='10dp', size_hint_y=None, adaptive_height=True, padding=['20dp', '20dp', '20dp', '10dp'])
        content.add_widget(MDIcon(icon='shield-check', halign='center', font_size='60sp', theme_text_color='Custom', text_color=self.theme_cls.primary_color, pos_hint={'center_x': 0.5}))
        content.add_widget(MDLabel(text='Activation Requise', halign='center', font_style='H5', bold=True, theme_text_color='Primary', adaptive_height=True))
        id_card = MDCard(orientation='vertical', radius=[8], padding=['15dp', '10dp', '15dp', '10dp'], md_bg_color=(0.96, 0.96, 0.96, 1), elevation=0, size_hint_y=None, adaptive_height=True, spacing='5dp')
        id_card.add_widget(MDLabel(text="ID d'appareil :", halign='left', font_style='Caption', theme_text_color='Secondary', adaptive_height=True))
        id_row = MDBoxLayout(orientation='horizontal', spacing='10dp', adaptive_height=True)
        field_id = MDTextField(text=device_id, readonly=True, font_size='16sp', mode='line', active_line=False, size_hint_x=0.85, pos_hint={'center_y': 0.5})
        btn_copy = MDIconButton(icon='content-copy', theme_text_color='Custom', text_color=self.theme_cls.primary_color, on_release=lambda x: Clipboard.copy(device_id), pos_hint={'center_y': 0.5}, icon_size='20sp')
        id_row.add_widget(field_id)
        id_row.add_widget(btn_copy)
        id_card.add_widget(id_row)
        content.add_widget(id_card)
        key_row = MDBoxLayout(orientation='horizontal', spacing='10dp', adaptive_height=True)
        self.field_key = NoMenuTextField(hint_text='Clé de licence', mode='rectangle', size_hint_x=0.85, pos_hint={'center_y': 0.5})
        btn_paste = MDIconButton(icon='content-paste', theme_text_color='Custom', text_color=self.theme_cls.primary_color, on_release=lambda x: setattr(self.field_key, 'text', Clipboard.paste()), pos_hint={'center_y': 0.5}, icon_size='20sp')
        key_row.add_widget(self.field_key)
        key_row.add_widget(btn_paste)
        content.add_widget(key_row)
        btn_activate = MDRaisedButton(text="ACTIVER L'APPLICATION", md_bg_color=(0, 0.7, 0, 1), font_size='16sp', elevation=0, size_hint_x=1, size_hint_y=None, height='50dp', on_release=lambda x: self.validate_activation(self.field_key.text, self.activation_dialog_ref))
        content.add_widget(btn_activate)
        self.activation_dialog_ref = MDDialog(title='', type='custom', content_cls=content, size_hint=(0.9, None), auto_dismiss=False, radius=[16, 16, 16, 16])
        self.activation_dialog_ref.open()

    def on_start(self):
        if self.check_license_validity():
            Clock.schedule_once(self._deferred_start, 0.5)
        else:
            Clock.schedule_once(lambda dt: self.show_activation_dialog(), 0.5)

    def _deferred_start(self, dt):
        threading.Thread(target=self.check_server_heartbeat, daemon=True).start()
        try:
            if self.store.exists('session'):
                session = self.store.get('session')
                if session.get('logged_in'):
                    self.current_user_name = session.get('username', 'ADMIN')
                    self.screen_manager.current = 'tables'
                    self.fetch_tables()
                    self.start_refresh()
        except:
            pass

    def check_server_heartbeat(self):
        while not self.stop_heartbeat:
            self._run_socket_ping_logic()
            time.sleep(3)

    def _run_socket_ping_logic(self):
        success = False
        target_ip = self.local_server_ip
        duration = 0
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.5)
            start_t = time.time()
            result = sock.connect_ex((target_ip, int(DEFAULT_PORT)))
            if result == 0:
                duration = (time.time() - start_t) * 1000
                success = True
                self.active_server_ip = target_ip
            elif self.external_server_ip:
                target_ip = self.external_server_ip
                result_ext = sock.connect_ex((target_ip, int(DEFAULT_PORT)))
                if result_ext == 0:
                    duration = (time.time() - start_t) * 1000
                    success = True
                    self.active_server_ip = target_ip
        except:
            success = False
        finally:
            if sock:
                sock.close()
        self.is_server_reachable = success
        self.server_ip = self.active_server_ip
        Clock.schedule_once(lambda dt: self.update_status_bar_safe(success, duration, self.server_ip), 0)

    def update_status_bar_safe(self, connected, ping_ms, ip_used):
        if not self.status_bar_label:
            return
        if connected:
            if ping_ms < 200:
                color = (0, 0.6, 0.2, 1)
            elif ping_ms < 800:
                color = (0.9, 0.6, 0.1, 1)
            else:
                color = (0.8, 0.1, 0.1, 1)
            self.status_bar_label.text = f'Connecté - {int(ping_ms)}ms'
            self.status_bar_box.md_bg_color = color
        else:
            self.status_bar_label.text = 'Déconnecté'
            self.status_bar_box.md_bg_color = (0.8, 0.1, 0.1, 1)

    def build(self):
        Config.set('kivy', 'log_level', 'error')
        Config.write()
        Builder.load_string(KV_BUILDER)
        self.title = 'MagPro Mobile'
        self.theme_cls.primary_palette = 'Teal'
        self.theme_cls.primary_hue = '700'
        self.theme_cls.theme_style = 'Light'
        self.theme_cls.font_styles['H5'] = ['ArabicFont', 24, False, 0]
        self.theme_cls.font_styles['Subtitle1'] = ['ArabicFont', 16, False, 0.15]
        self.theme_cls.font_styles['Body2'] = ['ArabicFont', 14, False, 0.25]
        self.theme_cls.font_styles['Caption'] = ['ArabicFont', 12, False, 0.4]
        self.data_dir = self.user_data_dir
        self.offline_store = JsonStore(os.path.join(self.data_dir, 'pending_orders.json'))
        self.cache_store = JsonStore(os.path.join(self.data_dir, 'app_cache.json'))
        log_path = os.path.join(self.data_dir, 'magpro.log')
        logging.basicConfig(filename=log_path, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s', force=True)
        self.store = JsonStore(os.path.join(self.data_dir, 'app_settings.json'))
        self.image_cache = ImageCacheManager(base_dir=self.data_dir)
        if self.store.exists('config'):
            cfg = self.store.get('config')
            self.local_server_ip = cfg.get('ip', '192.168.1.100')
            self.external_server_ip = cfg.get('ext_ip', '')
            self.server_ip = self.local_server_ip
        if self.store.exists('user'):
            self.current_user_name = self.store.get('user')['name']
        self.ws_manager = WebSocketManager(self.server_ip, DEFAULT_PORT, self.on_websocket_message, on_connect_callback=lambda: self.notify('Connecté au serveur', 'info'), on_disconnect_callback=lambda: self.notify('Connexion au serveur perdue', 'error'))
        root_layout = MDBoxLayout(orientation='vertical')
        self.screen_manager = MDScreenManager()
        root_layout.add_widget(self.screen_manager)
        self.status_bar_box = MDBoxLayout(size_hint_y=None, height=dp(40), md_bg_color=(0.2, 0.2, 0.2, 1), padding=[dp(10), 0])
        self.status_bar_label = MDLabel(text='Prêt', halign='center', valign='middle', theme_text_color='Custom', text_color=(1, 1, 1, 1), font_style='Subtitle1', bold=True, font_name='ArabicFont')
        self.status_bar_box.add_widget(self.status_bar_label)
        root_layout.add_widget(self.status_bar_box)
        screen_login = MDScreen(name='login')
        background_layout = MDFloatLayout()
        top_bg = MDBoxLayout(size_hint=(1, 0.5), pos_hint={'top': 1}, md_bg_color=self.theme_cls.primary_color)
        background_layout.add_widget(top_bg)
        settings_btn = MDIconButton(icon='cog', theme_text_color='Custom', text_color=(1, 1, 1, 1), pos_hint={'top': 0.98, 'right': 0.98}, on_release=self.open_ip_settings)
        background_layout.add_widget(settings_btn)
        card_login = MDCard(orientation='vertical', size_hint=(0.85, None), height=dp(400), pos_hint={'center_x': 0.5, 'center_y': 0.5}, padding=dp(30), spacing=dp(20), radius=[20], elevation=10, md_bg_color=(1, 1, 1, 1))
        icon_box = MDBoxLayout(size_hint_y=None, height=dp(80), pos_hint={'center_x': 0.5})
        main_icon = MDIcon(icon='silverware-variant', font_size='70sp', theme_text_color='Custom', text_color=self.theme_cls.primary_color, pos_hint={'center_x': 0.5, 'center_y': 0.5})
        icon_box.add_widget(main_icon)
        card_login.add_widget(icon_box)
        title_label = MDLabel(text='MagPro Restaurant', halign='center', font_style='H5', theme_text_color='Primary', bold=True)
        card_login.add_widget(title_label)
        self.username_field = SmartTextField(text=self.current_user_name, hint_text="Nom d'utilisateur", icon_right='account', mode='rectangle')
        self.password_field = SmartTextField(hint_text='Mot de passe', icon_right='key', password=True, mode='rectangle')
        btn_login = MDFillRoundFlatButton(text='CONNEXION', font_size='18sp', size_hint_x=1, height=dp(50), on_release=self.do_login)
        card_login.add_widget(self.username_field)
        card_login.add_widget(self.password_field)
        card_login.add_widget(MDBoxLayout(size_hint_y=None, height=dp(10)))
        card_login.add_widget(btn_login)
        background_layout.add_widget(card_login)
        footer = MDLabel(text='MagPro v7.1.0.0 © 2026', halign='center', pos_hint={'bottom': 1, 'center_x': 0.5}, theme_text_color='Hint', font_style='Caption', size_hint_y=None, height=dp(30))
        background_layout.add_widget(footer)
        screen_login.add_widget(background_layout)
        self.screen_manager.add_widget(screen_login)
        screen_tables = MDScreen(name='tables')
        layout = MDBoxLayout(orientation='vertical')
        self.toolbar_tables = MDTopAppBar(title='Salles & Tables', right_action_items=[['cloud-sync-outline', lambda x: self.open_pending_orders_dialog()], ['refresh', lambda x: self.fetch_tables(manual=True)], ['logout', lambda x: self.confirm_logout()]], elevation=2)
        layout.add_widget(self.toolbar_tables)
        self.scroll_tables = MDScrollView()
        self.grid_tables = MDGridLayout(cols=2, padding=dp(15), spacing=dp(15), size_hint_y=None, adaptive_height=True)
        self.scroll_tables.add_widget(self.grid_tables)
        layout.add_widget(self.scroll_tables)
        screen_tables.add_widget(layout)
        self.screen_manager.add_widget(screen_tables)
        screen_order = MDScreen(name='order')
        layout_o = MDBoxLayout(orientation='vertical')
        self.toolbar_order = MDTopAppBar(title='Prise de commande', left_action_items=[['arrow-left', lambda x: self.go_back()]], elevation=2)
        layout_o.add_widget(self.toolbar_order)
        search_box = MDBoxLayout(padding=(15, 5, 15, 5), size_hint_y=None, height=dp(65))
        self.search_field = SmartTextField(hint_text='Rechercher article...', mode='rectangle', icon_right='magnify')
        self.search_field.bind(text=self.filter_products_live)
        search_box.add_widget(self.search_field)
        layout_o.add_widget(search_box)
        self.rv_products = ProductRecycleView()
        layout_o.add_widget(self.rv_products)
        self.cart_area = MDBoxLayout(orientation='horizontal', padding=15, spacing=10, size_hint_y=None, height=dp(80))
        self.btn_reminder = MDFillRoundFlatIconButton(text='RAPPEL', icon='bell-ring', font_size='16sp', md_bg_color=(0.9, 0.5, 0.2, 1), size_hint_x=0.35, on_release=self.send_reminder)
        self.btn_cart = MDFillRoundFlatButton(text='VOIR PANIER (0)', font_size='18sp', size_hint_x=0.65, on_release=self.show_cart)
        self.cart_area.add_widget(self.btn_cart)
        layout_o.add_widget(self.cart_area)
        screen_order.add_widget(layout_o)
        self.screen_manager.add_widget(screen_order)
        Clock.schedule_once(lambda dt: self.ws_manager.connect(), 1)
        Window.bind(size=self.update_orientation_layout)
        Clock.schedule_once(lambda dt: self.update_orientation_layout(Window, Window.size), 1)
        return root_layout

    def filter_products_live(self, instance, text):
        if self._search_event:
            self._search_event.cancel()
        query = instance.get_value() if hasattr(instance, 'get_value') else text
        self._search_event = Clock.schedule_once(lambda dt: self._start_background_search(query), 0.4)

    def _start_background_search(self, query):
        threading.Thread(target=self._search_worker, args=(query,), daemon=True).start()

    def _search_worker(self, query):
        if not query or not query.strip():
            Clock.schedule_once(lambda dt: self.prepare_products_for_rv(self.all_products), 0)
            return
        query_clean = query.lower().strip()
        query_tokens = query_clean.split()
        filtered = []
        for p in self.all_products:
            p_name = str(p.get('name', '')).lower()
            if all((token in p_name for token in query_tokens)):
                filtered.append(p)
        Clock.schedule_once(lambda dt: self.prepare_products_for_rv(filtered), 0)

    def prepare_products_for_rv(self, products_list):
        self.current_product_list_source = products_list
        self.displayed_products_count = 0
        self.is_loading_more = False
        if self.rv_products:
            Clock.schedule_once(lambda dt: self.load_more_products(reset=True), 0)

    def load_more_products(self, reset=False):
        if self.is_loading_more and (not reset):
            return
        total_items = len(self.current_product_list_source)
        if self.displayed_products_count >= total_items and (not reset):
            return
        self.is_loading_more = True
        if reset:
            self.displayed_products_count = 0
        start = self.displayed_products_count
        end = start + self.PRODUCTS_PER_PAGE
        if end > total_items:
            end = total_items
        batch_to_load = self.current_product_list_source[start:end]
        self._process_batch_data(batch_to_load, reset)

    def _process_batch_data(self, batch, reset=False):
        rv_data = []
        for p in batch:
            raw_name = str(p.get('name', 'Inconnu'))
            display_name = self.fix_text(raw_name)
            try:
                price_val = int(float(p.get('price', 0)))
            except:
                price_val = 0
            image_filename = p.get('image')
            full_image_url = ''
            if image_filename:
                safe_filename = urllib.parse.quote(image_filename)
                key_url = f'http://server/api/images/{safe_filename}'
                cached_path = self.image_cache.get_cache_path(key_url)
                if cached_path and os.path.exists(cached_path):
                    full_image_url = cached_path
                elif self.is_server_reachable:
                    full_image_url = f'http://{self.server_ip}:{DEFAULT_PORT}/api/images/{safe_filename}'
                    t = threading.Thread(target=self._cache_image_worker, args=(full_image_url,), daemon=True)
                    t.start()
            rv_data.append({'name_display': display_name, 'price_display': f'{price_val} DA', 'image_url': full_image_url, 'raw_data': p})
        self._update_rv_data(rv_data, reset)

    @mainthread
    def _update_rv_data(self, rv_data, reset):
        if self.rv_products:
            if reset:
                self.rv_products.data = rv_data
                self.displayed_products_count = len(rv_data)
            else:
                self.rv_products.data.extend(rv_data)
                self.displayed_products_count += len(rv_data)
            self.rv_products.refresh_from_data()
        self.is_loading_more = False

    def _cache_image_worker(self, url):
        try:
            path = self.image_cache.get_cache_path(url)
            if not path or os.path.exists(path):
                return
            temp_path = path + '.tmp'
            with urllib.request.urlopen(url, timeout=7) as response:
                if response.status == 200:
                    with open(temp_path, 'wb') as f:
                        f.write(response.read())
                    os.rename(temp_path, path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logging.error(f'Image Cache Error: {e}')

    def toggle_reminder_button(self, show=False):
        if self.btn_reminder.parent:
            self.cart_area.remove_widget(self.btn_reminder)
        if self.btn_cart.parent:
            self.cart_area.remove_widget(self.btn_cart)
        if show:
            self.btn_cart.size_hint_x = 0.65
            self.btn_reminder.size_hint_x = 0.35
            self.cart_area.add_widget(self.btn_cart)
            self.cart_area.add_widget(self.btn_reminder)
        else:
            self.btn_cart.size_hint_x = 1.0
            self.cart_area.add_widget(self.btn_cart)

    def send_reminder(self, instance):
        if self.is_offline_mode:
            self.notify("Impossible d'envoyer un rappel en mode hors ligne", 'error')
            return
        data = {'table_id': self.current_table['id'], 'seat_number': self.current_seat, 'user_name': self.current_user_name}
        self.notify('Envoi du rappel en cours...', 'info')
        UrlRequest(f'http://{self.server_ip}:{DEFAULT_PORT}/api/remind_order', req_body=json.dumps(data), req_headers={'Content-type': 'application/json'}, method='POST', on_success=lambda r, res: self.notify('Rappel envoyé en cuisine avec succès', 'success'), on_failure=lambda r, e: self.notify("Échec de l'envoi du rappel", 'error'), on_error=lambda r, e: self.notify('Erreur de connexion', 'error'), timeout=5)

    def initiate_move(self, table_info):
        UrlRequest(f"http://{self.server_ip}:{DEFAULT_PORT}/api/table_seats/{table_info['id']}", on_success=lambda r, res: self._show_move_options_dialog(table_info, res), on_error=lambda r, e: self.notify('Échec de connexion au serveur', 'error'))

    def _show_move_options_dialog(self, table_info, occupied_dict):
        if not occupied_dict:
            self.notify('Table vide, rien à transférer', 'warning')
            return
        content = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=dp(10), padding=dp(10))
        if '0' in occupied_dict:
            btn = MDRaisedButton(text=f"Transférer TOUTE la table ({table_info['name']})", size_hint_x=1, md_bg_color=(0.9, 0.5, 0.2, 1), on_release=lambda x: self._start_move_and_close(table_info, 0))
            content.add_widget(btn)
        else:
            content.add_widget(MDLabel(text="Choisir l'élément à déplacer :", halign='center', bold=True))
            for seat_num, data in occupied_dict.items():
                btn = MDRaisedButton(text=f"Transférer Chaise {seat_num} ({int(float(data['amount']))} DA)", size_hint_x=1, on_release=lambda x, s=int(seat_num): self._start_move_and_close(table_info, s))
                content.add_widget(btn)
        self.dialog_move_select = MDDialog(title='Options de Transfert', type='custom', content_cls=content, buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: self.dialog_move_select.dismiss())])
        self.dialog_move_select.open()

    def _start_move_and_close(self, table_info, seat_num):
        if self.dialog_move_select:
            self.dialog_move_select.dismiss()
        self._start_move_mode(table_info, seat_num)

    def _show_seat_selection_for_move(self, table_info, occupied_seats):
        if self.dialog_move_select:
            self.dialog_move_select.dismiss()
        content = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=10)
        for seat in occupied_seats:
            btn = MDRaisedButton(text=f'Déplacer Chaise {seat}', size_hint_x=1, on_release=lambda x, s=seat: self._confirm_seat_selection(table_info, s))
            content.add_widget(btn)
        self.dialog_move_select = MDDialog(title=f"Transfert depuis {table_info['name']}", type='custom', content_cls=content, buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: self.dialog_move_select.dismiss())])
        self.dialog_move_select.open()

    def _confirm_seat_selection(self, table_info, seat_num):
        if self.dialog_move_select:
            self.dialog_move_select.dismiss()
        self._start_move_mode(table_info, seat_num)

    def _start_move_mode(self, table_info, seat_num):
        self.move_mode = True
        self.move_source_data = {'table': table_info, 'seat': seat_num}
        what = 'la table' if seat_num == 0 else f'la chaise {seat_num}'
        self.notify(f"Déplacement de {what} de {table_info['name']}... Sélectionnez la destination", 'info')
        self.toolbar_tables.title = 'Mode Transfert...'
        self.toolbar_tables.md_bg_color = (0.9, 0.5, 0.2, 1)

    def process_destination_selection(self, dest_table):
        if not self.move_mode:
            return
        source = self.move_source_data['table']
        source_seat = self.move_source_data['seat']
        if source['id'] == dest_table['id']:
            self.notify('Destination identique à la source !', 'error')
            self.cancel_move()
            return
        UrlRequest(f"http://{self.server_ip}:{DEFAULT_PORT}/api/table_seats/{dest_table['id']}", on_success=lambda r, res: self._decide_final_move(source, source_seat, dest_table, res), on_error=lambda r, e: self.notify('Erreur de vérification destination', 'error'))

    def _decide_final_move(self, source, source_seat, dest_table, dest_seats_dict):
        if dest_seats_dict:
            self.notify('Action refusée : Table de destination occupée', 'error')
            self.cancel_move()
        else:
            self.show_empty_table_mode_dialog(source, source_seat, dest_table)

    def show_empty_table_mode_dialog(self, source, source_seat, dest_table):
        if self.dialog_empty_options:
            self.dialog_empty_options.dismiss()
        what = 'Tout' if source_seat == 0 else f'Chaise {source_seat}'
        content = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=15, padding=[0, 10, 0, 0])
        btn_entire = MDRaisedButton(text='TABLE ENTIÈRE (GROUPE)', md_bg_color=(0.2, 0.6, 0.8, 1), size_hint_x=1, on_release=lambda x: self._confirm_move_choice(source, source_seat, dest_table, 0))
        btn_chair = MDRaisedButton(text='CHAISE INDIVIDUELLE', md_bg_color=(0.3, 0.7, 0.3, 1), size_hint_x=1, on_release=lambda x: self._confirm_move_choice(source, source_seat, dest_table, 1))
        content.add_widget(btn_entire)
        content.add_widget(btn_chair)
        self.dialog_empty_options = MDDialog(title=f"Vers {dest_table['name']} (Vide)", text=f'Comment voulez-vous installer {what} ?', type='custom', content_cls=content, buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: self.dialog_empty_options.dismiss())])
        self.dialog_empty_options.open()

    def _confirm_move_choice(self, source, source_seat, dest_table, target_seat):
        if self.dialog_empty_options:
            self.dialog_empty_options.dismiss()
        self.show_move_confirmation(source, source_seat, dest_table, target_seat)

    def _confirm_empty_choice(self, source, source_seat, dest_table, chosen_target_seat):
        if self.dialog_empty_options:
            self.dialog_empty_options.dismiss()
        self.show_move_confirmation(source, source_seat, dest_table, target_seat=chosen_target_seat)

    def show_move_confirmation(self, source, source_seat, dest, target_seat=1):
        what = 'toute la table' if source_seat == 0 else f'la chaise {source_seat}'
        target_desc = 'Table entière' if target_seat == 0 else 'Chaise individuelle'
        dialog = MDDialog(title='Confirmer le transfert', text=f"Transférer {what} de '{source['name']}' vers '{dest['name']}' ?\n\nMode : {target_desc}", buttons=[MDFlatButton(text='NON', on_release=lambda x: self.cancel_move_dialog(dialog)), MDRaisedButton(text='OUI', on_release=lambda x: self.execute_move(source, source_seat, dest, dialog, target_seat))])
        dialog.open()

    def cancel_move_dialog(self, dialog):
        dialog.dismiss()
        self.cancel_move(show_notification=True)

    def execute_move(self, source, source_seat, dest, dialog, target_seat=1):
        dialog.dismiss()
        if source_seat == 0 and target_seat == 0:
            url = f'http://{self.server_ip}:{DEFAULT_PORT}/api/move_table'
            data = {'source_id': source['id'], 'dest_id': dest['id']}
        else:
            url = f'http://{self.server_ip}:{DEFAULT_PORT}/api/move_seat'
            data = {'table_id': source['id'], 'source_seat': source_seat, 'dest_table_id': dest['id'], 'dest_seat': target_seat}
        self.notify('Transfert en cours...', 'info')
        UrlRequest(url, req_body=json.dumps(data), req_headers={'Content-type': 'application/json'}, method='POST', on_success=lambda r, res: self.on_move_success(res), on_failure=lambda r, e: self.notify('Le serveur a rejeté le transfert', 'error'), on_error=lambda r, e: self.notify('Erreur réseau / serveur', 'error'), timeout=5)

    def on_move_success(self, res):
        if res.get('status') == 'success':
            self.notify('Transfert effectué avec succès ✅', 'success')
        else:
            msg = res.get('message', 'Échec du transfert')
            self.notify(msg, 'error')
        self.cancel_move(show_notification=False)

    def cancel_move(self, show_notification=True):
        self.move_mode = False
        self.move_source_data = None
        if show_notification:
            self.notify('Transfert annulé', 'info')
        self.toolbar_tables.title = 'Salles & Tables'
        self.toolbar_tables.md_bg_color = self.theme_cls.primary_color
        self.fetch_tables(manual=True)

    def notify(self, message, type='info'):
        if not self.status_bar_box:
            return
        message = self.fix_text(message)
        colors = {'success': (0.1, 0.6, 0.2, 1), 'error': (0.75, 0.2, 0.2, 1), 'warning': (0.9, 0.6, 0.1, 1), 'info': (0.2, 0.4, 0.6, 1)}
        if self.status_bar_timer:
            self.status_bar_timer.cancel()
        self.status_bar_label.text = message
        self.status_bar_box.md_bg_color = colors.get(type, (0.2, 0.2, 0.2, 1))
        self.status_bar_timer = Clock.schedule_once(self.reset_status_bar, 4)

    def reset_status_bar(self, dt):
        if self.status_bar_box:
            if self.is_server_reachable:
                self.status_bar_label.text = 'Connecté'
                self.status_bar_box.md_bg_color = (0, 0.6, 0.2, 1)
            else:
                self.status_bar_label.text = 'Déconnecté'
                self.status_bar_box.md_bg_color = (0.8, 0.1, 0.1, 1)

    def on_stop(self):
        self.stop_heartbeat = True
        if self.ws_manager:
            self.ws_manager.disconnect()

    def on_websocket_message(self, data):
        msg_type = data.get('type')
        if msg_type == 'tables_update':
            Clock.schedule_once(lambda dt: self.fetch_tables(), 0)

    def hash_password(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def standard_error_handler(self, req, error, custom_msg=None, fatal=False):
        self.request_pending = False
        err_str = str(error).lower()
        msg = custom_msg or 'Erreur de connexion.'
        if 'connecttimeout' in err_str or 'etimedout' in err_str:
            msg = 'Le serveur ne répond pas (Délai dépassé).'
        elif 'connection refused' in err_str or 'econnrefused' in err_str:
            msg = "Connexion refusée. Vérifiez l'adresse IP."
        elif 'no route to host' in err_str or 'ehostunreach' in err_str:
            msg = 'Serveur introuvable. Vérifiez votre réseau Wi-Fi.'
        elif 'socket' in err_str:
            msg = 'Erreur réseau (Socket). Vérifiez la connexion.'
        logging.error(f'Network Error: {err_str}')
        if not fatal:
            self.notify(msg, 'error')
        else:
            self.show_fatal_error(msg)

    def show_fatal_error(self, msg):
        dialog = MDDialog(title='Erreur Critique', text=msg, buttons=[MDFlatButton(text='OK', on_release=lambda x: dialog.dismiss())])
        dialog.open()

    def open_ip_settings(self, instance=None):
        content = MDBoxLayout(orientation='vertical', spacing='12dp', size_hint_y=None, height='140dp')
        self.ip_field_dialog = MDTextField(text=self.local_server_ip, hint_text='IP Locale', mode='rectangle')
        self.ext_ip_field_dialog = MDTextField(text=self.external_server_ip, hint_text='IP Externe (Optionnel)', mode='rectangle')
        content.add_widget(self.ip_field_dialog)
        content.add_widget(self.ext_ip_field_dialog)
        self.dialog_ip = MDDialog(title='Configuration Serveur', type='custom', content_cls=content, buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: self.dialog_ip.dismiss()), MDRaisedButton(text='ENREGISTRER', on_release=self.save_ip_settings)])
        self.dialog_ip.open()

    def save_ip_settings(self, instance):
        new_local = self.ip_field_dialog.text.strip()
        new_ext = self.ext_ip_field_dialog.text.strip()
        if not DataValidator.validate_ip(new_local):
            self.notify('IP Locale invalide.', 'error')
            return
        self.local_server_ip = new_local
        self.external_server_ip = new_ext
        self.active_server_ip = new_local
        self.server_ip = new_local
        self.store.put('config', ip=new_local, ext_ip=new_ext)
        self.notify('Configuration sauvegardée.', 'success')
        if self.dialog_ip:
            self.dialog_ip.dismiss()
        self.fetch_tables(manual=True)

    def do_login(self, instance):
        username = self.username_field.get_value().strip()
        password = self.password_field.get_value().strip()
        if not username:
            self.notify("Nom d'utilisateur requis.", 'warning')
            return
        url = f'http://{self.server_ip}:{DEFAULT_PORT}/api/login'
        headers = {'Content-type': 'application/json'}
        body = json.dumps({'username': username, 'password': password})
        UrlRequest(url, req_body=body, req_headers=headers, method='POST', on_success=self.login_success_handler, on_failure=lambda r, e: self.notify('Identifiants incorrects.', 'error'), on_error=lambda r, e: self.standard_error_handler(r, e, 'Serveur de connexion inaccessible.'), timeout=5)

    def login_success_handler(self, req, result):
        if result.get('status') == 'success':
            self.current_user_name = self.username_field.text.strip()
            self.store.put('user', name=self.current_user_name)
            self.store.put('session', logged_in=True, username=self.current_user_name)
            if 'token' in result:
                self.auth_token = result['token']
                self.token_expiry = datetime.now() + timedelta(minutes=self.TOKEN_LIFETIME)
            self.notify(f'Authentification réussie. Bienvenue {self.current_user_name}.', 'success')
            self.screen_manager.current = 'tables'
            self.fetch_tables()
            self.start_refresh()
        else:
            self.notify('Échec de la connexion.', 'error')

    def confirm_logout(self):
        dialog = MDDialog(title='Déconnexion', text='Voulez-vous vraiment vous déconnecter ?', buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: dialog.dismiss()), MDRaisedButton(text='DÉCONNEXION', md_bg_color=(0.8, 0, 0, 1), on_release=lambda x: self.perform_logout(dialog))])
        dialog.open()

    def perform_logout(self, dialog):
        dialog.dismiss()
        self.logout()

    def logout(self):
        self.stop_refresh()
        if self.store.exists('session'):
            self.store.put('session', logged_in=False, username=self.current_user_name)
        self.screen_manager.current = 'login'
        self.password_field.text = ''
        self.notify('Déconnecté', 'info')

    def start_refresh(self):
        self.stop_refresh()
        self.refresh_event = Clock.schedule_interval(self.silent_refresh, self.REFRESH_RATE)

    def stop_refresh(self):
        if self.refresh_event:
            self.refresh_event.cancel()
            self.refresh_event = None

    def fetch_tables(self, manual=False):
        if self.request_pending:
            return
        self.request_pending = True
        if self.cache_store.exists('tables'):
            cached_tables = self.cache_store.get('tables')['data']
            self.update_tables(None, cached_tables)

        def on_success(req, result):
            self.is_offline_mode = False
            self.update_tables(req, result)
            self.cache_store.put('tables', data=result)
            self._cache_all_tables_details(result)
            self.process_offline_queue()

        def on_error(req, error):
            self.request_pending = False
            self.is_offline_mode = True
            if not self.cache_store.exists('tables') and manual:
                self.standard_error_handler(req, error, "Impossible d'actualiser les tables.")
        UrlRequest(f'http://{self.server_ip}:{DEFAULT_PORT}/api/tables', on_success=on_success, on_error=on_error, on_failure=on_error, timeout=3)

    def _cache_all_tables_details(self, tables):
        for t in tables:
            tid = t['id']
            UrlRequest(f'http://{self.server_ip}:{DEFAULT_PORT}/api/table_seats/{tid}', on_success=lambda r, res, table_id=tid: self.cache_store.put(f'seats_{table_id}', data=res), on_error=self.silent_error, timeout=10)

    def silent_error(self, req, error):
        self.request_pending = False

    def silent_refresh(self, dt):
        pending_count = len(self.offline_store.keys())
        if pending_count > 0:
            if hasattr(self, 'toolbar_tables'):
                self.toolbar_tables.right_action_items[0] = ['cloud-sync-outline', lambda x: self.open_pending_orders_dialog()]
        if self.screen_manager.current == 'tables':
            if self.request_pending:
                return
            self.fetch_tables()

    def update_tables(self, req, result):
        self.request_pending = False
        if not result:
            return
        try:
            sorted_tables = sorted(result, key=lambda x: x['name'])
            new_ids = {str(t['id']) for t in sorted_tables}
            existing_ids = list(self.table_widgets.keys())
            for tid in existing_ids:
                if tid not in new_ids:
                    widget = self.table_widgets.pop(tid)
                    self.grid_tables.remove_widget(widget)

            def update_chunk(dt, tables_list, index=0):
                chunk_size = 5
                end_index = min(index + chunk_size, len(tables_list))
                for i in range(index, end_index):
                    t_data = tables_list[i]
                    tid = str(t_data['id'])
                    try:
                        table_total = float(t_data.get('total', 0))
                    except:
                        table_total = 0.0
                    if t_data['status'] == 'occupied' and table_total <= 0:
                        t_data['status'] = 'available'
                    if tid in self.table_widgets:
                        if self.table_widgets[tid].table.get('status') != t_data['status'] or self.table_widgets[tid].table.get('total') != t_data.get('total'):
                            self.table_widgets[tid].update_state(t_data)
                    else:
                        new_card = TableCard(t_data, self)
                        self.table_widgets[tid] = new_card
                        self.grid_tables.add_widget(new_card)
                if end_index < len(tables_list):
                    Clock.schedule_once(lambda dt: update_chunk(dt, tables_list, end_index), 0.01)
            update_chunk(0, sorted_tables)
        except Exception as e:
            logging.error(f'Update tables error: {e}')

    def open_pending_orders_dialog(self):
        keys = list(self.offline_store.keys())
        if not keys:
            self.notify('Aucune commande en attente de synchronisation.', 'info')
            return
        self.pending_list_container = MDBoxLayout(orientation='vertical', adaptive_height=True)
        scroll = MDScrollView(size_hint_y=None, height=dp(300))
        scroll.add_widget(self.pending_list_container)
        self.refresh_pending_dialog_content()
        self.dialog_pending = MDDialog(title='Commandes Hors Ligne', type='custom', content_cls=scroll, buttons=[MDFlatButton(text='FERMER', on_release=lambda x: self.dialog_pending.dismiss())])
        self.dialog_pending.open()

    def refresh_pending_dialog_content(self):
        if not self.pending_list_container:
            return
        self.pending_list_container.clear_widgets()
        keys = list(self.offline_store.keys())
        if not keys:
            self.pending_list_container.add_widget(MDLabel(text='Toutes les commandes ont été synchronisées !', halign='center', theme_text_color='Hint'))
            return
        for key in keys:
            data = self.offline_store.get(key)['order_data']
            table_name = 'Table Inconnue'
            if self.cache_store.exists('tables'):
                tables = self.cache_store.get('tables')['data']
                for t in tables:
                    if t['id'] == data['table_id']:
                        table_name = t['name']
                        break
            seat_info = 'Groupe' if data['seat_number'] == 0 else f"Chaise {data['seat_number']}"
            total_price = sum((item['price'] * item['qty'] for item in data['items']))
            item_box = MDCard(orientation='horizontal', size_hint_y=None, height=dp(60), padding=dp(10), radius=[8], elevation=1, md_bg_color=(0.95, 0.95, 0.95, 1))
            info_layout = MDBoxLayout(orientation='vertical', size_hint_x=0.7)
            info_layout.add_widget(MDLabel(text=f'{table_name} - {seat_info}', bold=True, theme_text_color='Primary'))
            info_layout.add_widget(MDLabel(text=f"{len(data['items'])} articles | {int(total_price)} DA", theme_text_color='Secondary', font_style='Caption'))
            icon = MDIcon(icon='cloud-off-outline', theme_text_color='Custom', text_color=(0.8, 0.4, 0.4, 1), pos_hint={'center_y': 0.5})
            item_box.add_widget(info_layout)
            item_box.add_widget(icon)
            self.pending_list_container.add_widget(item_box)
            self.pending_list_container.add_widget(MDBoxLayout(size_hint_y=None, height=dp(5)))

    def show_chairs_dialog(self, table):
        self.stop_refresh()
        self.current_table = table
        try:
            chair_count = int(table.get('chairs', 0))
        except:
            chair_count = 0
        if chair_count == 0:
            self.open_seat_order(0)
            return
        url = f"http://{self.server_ip}:{DEFAULT_PORT}/api/table_seats/{table['id']}"

        def on_success(req, res):
            self.cache_store.put(f"seats_{table['id']}", data=res)
            if '0' in res:
                self.open_seat_order(0)
            else:
                self._build_chairs_dialog(table, res)
        UrlRequest(url, on_success=on_success, on_error=lambda r, e: self._load_seats_offline(table), timeout=2)

    def _build_chairs_dialog(self, table, seats_status):
        if self.dialog_chairs:
            self.dialog_chairs.dismiss()
        self.current_table = table
        try:
            chair_count = int(table.get('chairs', 4))
        except:
            chair_count = 4
        content = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=dp(10), padding=[0, 10, 0, 0])
        group_status = seats_status.get('0')
        group_bg = (0.9, 0.3, 0.3, 1) if group_status else (0.2, 0.6, 0.8, 1)
        try:
            amount = int(float(group_status['amount'])) if group_status else 0
        except:
            amount = 0
        card_group = MDCard(size_hint_y=None, height=dp(70), radius=[12], md_bg_color=group_bg, ripple_behavior=True)
        box_g = MDBoxLayout(orientation='horizontal', padding=10, spacing=10)
        box_g.add_widget(MDIcon(icon='account-group', theme_text_color='Custom', text_color=(1, 1, 1, 1), font_size='32sp', pos_hint={'center_y': 0.5}))
        box_g.add_widget(MDLabel(text=f'GROUPE\n{amount} DA' if amount > 0 else 'GROUPE', halign='center', bold=True, theme_text_color='Custom', text_color=(1, 1, 1, 1)))
        if group_status:
            btn_move = MDIconButton(icon='swap-horizontal', theme_text_color='Custom', text_color=(1, 1, 1, 1), on_release=lambda x: self.initiate_move_direct(table, 0))
            box_g.add_widget(btn_move)
        card_group.bind(on_release=lambda x: self.open_seat_order(0))
        card_group.add_widget(box_g)
        content.add_widget(card_group)
        content.add_widget(MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=(0.8, 0.8, 0.8, 1)))
        grid_chairs = MDGridLayout(cols=2, spacing=dp(10), adaptive_height=True)
        for i in range(1, chair_count + 1):
            s_stat = seats_status.get(str(i))
            is_busy = s_stat is not None
            c_color = (0.9, 0.3, 0.3, 1) if is_busy else (0.3, 0.7, 0.3, 1)
            try:
                amt = int(float(s_stat['amount'])) if is_busy else 0
            except:
                amt = 0
            card = MDCard(size_hint_y=None, height=dp(85), radius=[10], md_bg_color=c_color, ripple_behavior=True)
            card_box = MDBoxLayout(orientation='vertical', padding=5)
            row_header = MDBoxLayout(size_hint_y=None, height=dp(30))
            row_header.add_widget(MDIcon(icon='seat', theme_text_color='Custom', text_color=(1, 1, 1, 1), font_size='22sp'))
            if is_busy:
                btn_sw = MDIconButton(icon='swap-horizontal', icon_size='18sp', theme_text_color='Custom', text_color=(1, 1, 1, 1), on_release=lambda x, s=i: self.initiate_move_direct(table, s))
                row_header.add_widget(btn_sw)
            card_box.add_widget(row_header)
            card_box.add_widget(MDLabel(text=f'Chaise {i}', halign='center', bold=True, theme_text_color='Custom', text_color=(1, 1, 1, 1), font_style='Caption'))
            card_box.add_widget(MDLabel(text=f'{amt} DA' if is_busy else 'Libre', halign='center', theme_text_color='Custom', text_color=(1, 1, 1, 1), font_style='Caption'))
            card.bind(on_release=lambda x, s=i: self.open_seat_order(s))
            card.add_widget(card_box)
            grid_chairs.add_widget(card)
        content.add_widget(grid_chairs)
        self.dialog_chairs = MDDialog(title=f"Table: {table['name']}", type='custom', content_cls=content)
        self.dialog_chairs.open()

    def initiate_move_direct(self, table_info, seat_num):
        if self.dialog_chairs:
            self.dialog_chairs.dismiss()
        self._start_move_mode(table_info, seat_num)

    def _on_seats_loaded(self, table, res):
        self._dialog_working = False
        self.cache_store.put(f"seats_{table['id']}", data=res)
        if self.dialog_chairs:
            pass
        else:
            self._build_chairs_dialog(table, res)

    def _on_seats_loaded(self, table, res):
        self.cache_store.put(f"seats_{table['id']}", data=res)
        self._build_chairs_dialog(table, res)

    def _load_seats_offline(self, table):
        try:
            chair_count = int(table.get('chairs', 0))
        except:
            chair_count = 0
        if chair_count == 0:
            self.open_seat_order(0)
            return
        key = f"seats_{table['id']}"
        if self.cache_store.exists(key):
            data = self.cache_store.get(key)['data']
            if '0' in data:
                self.open_seat_order(0)
            else:
                self._build_chairs_dialog(table, data)
        else:
            self.notify('Erreur : Données non disponibles hors ligne.', 'error')

    def open_seat_order(self, seat_num):
        if self.current_table is None:
            self.notify('Erreur : Veuillez sélectionner la table à nouveau.', 'error')
            if self.dialog_chairs:
                self.dialog_chairs.dismiss()
            return
        if self.dialog_chairs:
            self.dialog_chairs.dismiss()
        self.current_seat = seat_num
        self.stop_refresh()
        self.cart = []
        self.update_cart_btn()
        occ_list = self.current_table.get('occupied_seats', [])
        occ_list_str = [str(x) for x in occ_list]
        is_seat_occupied = str(seat_num) in occ_list_str
        self.toggle_reminder_button(show=is_seat_occupied)
        if seat_num == 0:
            self.toolbar_order.title = f"Table {self.current_table['name']}"
        else:
            self.toolbar_order.title = f"Table {self.current_table['name']} - Chaise {seat_num}"
        self.screen_manager.current = 'order'
        self.search_field.clear()
        self.load_products()
        if not self.is_offline_mode:
            UrlRequest(f'http://{self.server_ip}:{DEFAULT_PORT}/api/cart_details', req_body=json.dumps({'table_id': self.current_table['id'], 'seat_number': self.current_seat}), req_headers={'Content-type': 'application/json'}, method='POST', on_success=self.on_cart_loaded, on_error=self.silent_error, timeout=5)
        else:
            self.cart = []

    def on_cart_loaded(self, req, result):
        self.cart = []
        if result and isinstance(result, list):
            for item in result:
                if 'quantity' in item:
                    item['qty'] = float(item['quantity'])
                elif 'qty' not in item:
                    item['qty'] = 1.0
                self.cart.append(item)
        self.update_cart_btn()
        is_seat_occupied = len(self.cart) > 0
        self.toggle_reminder_button(show=is_seat_occupied)

    def load_products(self):
        if self.cache_store.exists('products'):
            cached_prods = self.cache_store.get('products')['data']
            self.update_prods(None, cached_prods)

        def on_success(req, result):
            self.update_prods(req, result)
            self.cache_store.put('products', data=result)

        def on_error(req, error):
            self.is_offline_mode = True
            if not self.cache_store.exists('products'):
                self.standard_error_handler(req, error, 'Impossible de charger les produits.')
        UrlRequest(f'http://{self.server_ip}:{DEFAULT_PORT}/api/products', on_success=on_success, on_error=on_error, on_failure=on_error, timeout=3)

    def update_prods(self, req, result):
        if result and isinstance(result, list):
            result = [p for p in result if str(p.get('name', '')).strip().lower() != 'autre article']
        try:
            sorted_res = sorted(result, key=lambda x: int(float(x.get('sold_count', 0))), reverse=True)
        except:
            sorted_res = result
        self.all_products = sorted_res
        self.prepare_products_for_rv(sorted_res)

    def open_add_note_dialog(self, product):
        content = MDBoxLayout(orientation='vertical', spacing=20, size_hint_y=None, height=dp(180))
        qty_box = MDBoxLayout(orientation='horizontal', spacing=10, adaptive_height=True, pos_hint={'center_x': 0.5})
        self.qty_field = MDTextField(text='1', hint_text='Quantité', input_filter='float', halign='center', font_size='26sp', size_hint_x=0.4)
        qty_box.add_widget(MDIconButton(icon='minus-box', icon_size='40sp', on_release=lambda x: self.dialog_qty_dec()))
        qty_box.add_widget(self.qty_field)
        qty_box.add_widget(MDIconButton(icon='plus-box', icon_size='40sp', theme_text_color='Custom', text_color=self.theme_cls.primary_color, on_release=lambda x: self.dialog_qty_inc()))
        self.note_field = SmartTextField(hint_text='Note (optionnel)', multiline=False)
        content.add_widget(qty_box)
        content.add_widget(self.note_field)
        prod_name = self.fix_text(product['name'])
        self.dialog_note = MDDialog(title=f'{prod_name}', type='custom', content_cls=content, buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: self.dialog_note.dismiss()), MDRaisedButton(text='AJOUTER', on_release=lambda x: self.confirm_add(product))])
        self.dialog_note.open()

    def dialog_qty_inc(self):
        try:
            current_qty = float(self.qty_field.text)
            self.qty_field.text = str(int(current_qty + 1))
        except ValueError:
            self.qty_field.text = '1'

    def dialog_qty_dec(self):
        try:
            val = float(self.qty_field.text)
            if val > 1:
                self.qty_field.text = str(int(val - 1))
        except ValueError:
            self.qty_field.text = '1'

    def confirm_add(self, product):
        try:
            qty = DataValidator.validate_quantity(self.qty_field.text)
        except ValueError as e:
            self.notify(str(e), 'error')
            return
        note = DataValidator.sanitize_note(self.note_field.get_value())
        existing = next((i for i in self.cart if i['id'] == product['id'] and i.get('note') == note), None)
        if existing:
            existing['qty'] += qty
        else:
            try:
                price = float(product['price'])
            except:
                price = 0.0
            self.cart.append({'id': product['id'], 'name': product['name'], 'price': price, 'qty': qty, 'note': note})
        self.dialog_note.dismiss()
        self.update_cart_btn()
        self.notify('Article ajouté au panier avec succès.', 'success')

    def update_cart_btn(self):
        try:
            total = sum((float(i.get('price', 0)) * float(i.get('qty', 0)) for i in self.cart if i))
            items_count = len(self.cart)
            self.btn_cart.text = f'PANIER ({items_count}) {int(total)} DA'
        except Exception as e:
            self.btn_cart.text = 'PANIER (0) 0 DA'

    def show_cart(self, instance=None):
        content = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(500))
        self.cart_list_container = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=dp(8), padding=dp(5))
        scroll = MDScrollView()
        scroll.add_widget(self.cart_list_container)
        content.add_widget(scroll)
        footer = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=dp(15))
        self.btn_confirm_cart = MDFillRoundFlatButton(text='CONFIRMER', font_size='24sp', size_hint_x=1, height=dp(60), on_release=self.send_order)
        footer.add_widget(self.btn_confirm_cart)
        footer.add_widget(MDFillRoundFlatButton(text='RETOUR', size_hint_x=1, md_bg_color=(0.2, 0.6, 0.9, 1), on_release=lambda x: self.dialog_cart.dismiss()))
        content.add_widget(footer)
        self.dialog_cart = MDDialog(title=self.fix_text('Votre Panier'), type='custom', content_cls=content, size_hint=(0.9, None))
        self.update_cart_content()
        self.dialog_cart.open()

    def update_cart_content(self):
        if not self.dialog_cart:
            return
        self.cart_list_container.clear_widgets()
        for item in self.cart:
            self.cart_list_container.add_widget(CartItemCard(item, self))
        self.update_cart_totals_live()

    def update_cart_totals_live(self):
        total = sum((float(i['price']) * float(i['qty']) for i in self.cart))
        if hasattr(self, 'btn_confirm_cart'):
            self.btn_confirm_cart.text = f'CONFIRMER ({int(total)} DA)'
        self.update_cart_btn()

    def remove_from_cart(self, item):
        if item in self.cart:
            self.cart.remove(item)
            self.update_cart_btn()
            self.update_cart_content()

    def open_edit_note_dialog(self, item):
        content = MDBoxLayout(orientation='vertical', spacing=20, size_hint_y=None, height=dp(100))
        self.edit_note_field = SmartTextField(text=item.get('note', ''), hint_text='Modifier note', multiline=False)
        content.add_widget(self.edit_note_field)
        self.dialog_edit_note = MDDialog(title='Modifier Note', type='custom', content_cls=content, buttons=[MDRaisedButton(text='OK', on_release=lambda x: self.save_edited_note(item))])
        self.dialog_edit_note.open()

    def save_edited_note(self, item):
        item['note'] = DataValidator.sanitize_note(self.edit_note_field.get_value())
        self.dialog_edit_note.dismiss()
        self.update_cart_content()

    def send_order(self, instance):
        if not self.cart or len(self.cart) == 0:
            self.notify('Le panier est vide, envoi impossible', 'warning')
            if self.dialog_cart:
                self.dialog_cart.dismiss()
            return
        data = {'table_id': self.current_table['id'], 'seat_number': self.current_seat, 'items': self.cart, 'user_name': self.current_user_name, 'timestamp': str(datetime.now())}

        def save_offline(req, error):
            order_key = f'order_{int(datetime.now().timestamp())}_{self.current_seat}'
            self.offline_store.put(order_key, order_data=data)
            self.notify('Mode Hors Ligne : Commande sauvegardée localement', 'warning')
            self.cart = []
            self.update_cart_btn()
            self.go_back()
            if self.dialog_cart:
                self.dialog_cart.dismiss()
        UrlRequest(f'http://{self.server_ip}:{DEFAULT_PORT}/api/submit_order', req_body=json.dumps(data), req_headers={'Content-type': 'application/json'}, method='POST', on_success=self.on_sent, on_failure=save_offline, on_error=save_offline, timeout=5)
        if self.dialog_cart:
            self.dialog_cart.dismiss()

    def on_sent(self, req, result):
        self.notify('Commande transmise en cuisine avec succès.', 'success')
        self.cart = []
        self.update_cart_btn()
        self.go_back()

    def process_offline_queue(self):
        keys = list(self.offline_store.keys())
        if not keys:
            if self.dialog_pending:
                self.refresh_pending_dialog_content()
            return
        key = keys[0]
        order_data = self.offline_store.get(key)['order_data']

        def on_sync_success(req, res):
            logging.info(f'Synced order {key}')
            self.offline_store.delete(key)
            if self.dialog_pending:
                self.refresh_pending_dialog_content()
            self.notify(f'Synchronisation effectuée. {len(keys) - 1} commandes restantes.', 'info')
            self.process_offline_queue()

        def on_sync_fail(req, err):
            logging.warning('Sync failed, will try later')
        logging.info(f'Syncing order {key}...')
        UrlRequest(f'http://{self.server_ip}:{DEFAULT_PORT}/api/submit_order', req_body=json.dumps(order_data), req_headers={'Content-type': 'application/json'}, method='POST', on_success=on_sync_success, on_failure=on_sync_fail, on_error=on_sync_fail, timeout=5)

    def on_fail(self, req, error):
        self.notify('Le serveur a rejeté la commande (Erreur 500).', 'error')

    def go_back(self):
        self.screen_manager.current = 'tables'
        self.cart = []
        self.update_cart_btn()
        Clock.schedule_once(lambda dt: self.fetch_tables(manual=True), 0.2)
        self.start_refresh()

    def update_orientation_layout(self, window, size):
        new_cols = 5 if size[0] > size[1] else 2
        if hasattr(self, 'grid_tables') and self.grid_tables:
            self.grid_tables.cols = new_cols
        if hasattr(self, 'rv_products') and self.rv_products:
            if self.rv_products.children:
                self.rv_products.children[0].cols = new_cols

if __name__ == '__main__':
    RestaurantApp().run()
