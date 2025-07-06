import importlib
import types
import inspect
import time
import sys

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.network.urlrequest import UrlRequest
from kivy.uix.screenmanager import ScreenManager, Screen

from kivymd.app import MDApp
from kivymd.color_definitions import colors
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
import certifi

# --- Custom Exceptions ---

class HookManagerError(Exception):
    def __init__(self, message, code):
        super().__init__(f"[{code}] {message}")
        self.code = code

class NotHookedError(HookManagerError):
    def __init__(self, target):
        super().__init__(f"Target '{target}' is not hooked.", "NotHooked")

class AlreadyHookedError(HookManagerError):
    def __init__(self, target):
        super().__init__(f"Target '{target}' is already hooked.", "AlreadyHooked")

class NotPatchedError(HookManagerError):
    def __init__(self, target):
        super().__init__(f"Target '{target}' is not patched.", "NotPatched")


# --- Hook Manager ---

class HookManager:
    def __init__(self):
        self.originals = {}   # {(module, attr_path): original_func}
        self.hooked = set()   # {target_path}

    def _resolve_target(self, target_path):
        parts = target_path.split('.')
        for i in range(len(parts), 0, -1):
            try:
                module_name = '.'.join(parts[:i])
                module = importlib.import_module(module_name)
                attr_path = parts[i:]
                return module, attr_path
            except ModuleNotFoundError:
                continue
        raise ModuleNotFoundError(f"Cannot import module from {target_path}")

    def _get_attr(self, obj, attr_path):
        for attr in attr_path:
            obj = getattr(obj, attr)
        return obj

    def _set_attr(self, obj, attr_path, value):
        for attr in attr_path[:-1]:
            obj = getattr(obj, attr)
        setattr(obj, attr_path[-1], value)

    def _log(self, msg):
        print(f"[HooksNotice] {msg}")

    def hook(self, target_path):
        module, attr_path = self._resolve_target(target_path)
        key = (module, tuple(attr_path))
        if key in self.originals:
            raise AlreadyHookedError(target_path)
        self.originals[key] = self._get_attr(module, attr_path)
        self.hooked.add(target_path)
        self._log(f"Hooked {target_path}")

    def patch_print(self, target_path, message="hi"):
        module, attr_path = self._resolve_target(target_path)
        key = (module, tuple(attr_path))
        if key not in self.originals:
            raise NotHookedError(target_path)

        original = self.originals[key]

        def wrapped(*args, **kwargs):
            print(message)
            return original(*args, **kwargs)

        self._set_attr(module, attr_path, wrapped)
        self._log(f"Patched {'.'.join(attr_path)} with print wrapper.")

    def patch_function(self, target_path, func):
        global WrapperinitEnd
        module, attr_path = self._resolve_target(target_path)
        key = (module, tuple(attr_path))
        if key not in self.originals:
            raise NotHookedError(target_path)

        self._log(f"Preparing wrapper for {'.'.join(attr_path)}:")
        print("[Loader] MLoader Modded V1.0")
        print("[Loader] MLoader -> Modest 1.0")
        time.sleep(1)

        func_globals = func.__globals__.copy()
        symbol_count = 0

        for name in dir(module):
            if not name.startswith("__"):
                try:
                    attr = getattr(module, name)
                    func_globals[name] = attr
                    symbol_count += 1
                    print(".", end="", flush=True)
                    if symbol_count % 30 == 0:
                        print()
                except Exception:
                    continue

        rebound = types.FunctionType(
            func.__code__,
            func_globals,
            func.__name__,
            func.__defaults__,
            func.__closure__,
        )

        self._set_attr(module, attr_path, rebound)
        print("\n[HooksNotice] Wrapper is ready and patched.")
        WrapperinitEnd = True

    def restore(self, target_path):
        module, attr_path = self._resolve_target(target_path)
        key = (module, tuple(attr_path))

        if key not in self.originals:
            raise NotHookedError(target_path)

        self._set_attr(module, attr_path, self.originals.pop(key))
        self.hooked.discard(target_path)
        self._log(f"Restored {target_path}")

    def unhook_target(self, target_path):
        module, attr_path = self._resolve_target(target_path)
        key = (module, tuple(attr_path))
        if key not in self.originals:
            raise NotHookedError(target_path)
        self.originals.pop(key)
        self.hooked.discard(target_path)
        self._log(f"Unhooked {target_path} (function left modified)")

    def unhook(self):
        if not self.originals:
            raise NotPatchedError("No hooks to remove.")
        for (module, attr_path), _ in self.originals.items():
            self._log(f"Unhooked {module.__name__}.{'.'.join(attr_path)}")
        self.originals.clear()
        self.hooked.clear()
        self._log("Unhooked all")

    def dump_functions(self, module):
        funcs = [name for name, obj in inspect.getmembers(module, inspect.isfunction)]
        for i, f in enumerate(funcs, 1):
            print(f"{i}. Function: {f}")


# --- Hook Utilities ---

class HookUtilities:
    def __init__(self, hook_manager=None):
        self.hook_manager = hook_manager or HookManager()

    def is_hooked(self, target_path):
        return target_path in self.hook_manager.hooked

    def list_hooks(self):
        return list(self.hook_manager.hooked)

    def scan_module_functions(self, module_name):
        try:
            module = importlib.import_module(module_name)
            return [name for name, obj in inspect.getmembers(module, inspect.isfunction)]
        except ModuleNotFoundError:
            print(f"[HookUtilities] Module '{module_name}' not found.")
            return []

    def get_original_function(self, target_path):
        module, attr_path = self.hook_manager._resolve_target(target_path)
        key = (module, tuple(attr_path))
        return self.hook_manager.originals.get(key, None)

    def safe_call(self, target_path, *args, **kwargs):
        try:
            module, attr_path = self.hook_manager._resolve_target(target_path)
            func = self.hook_manager._get_attr(module, attr_path)
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[HookUtilities] Error during safe_call to {target_path}: {e}")
            return None


# Global optional state
WrapperinitEnd = False

# A placeholder target package name you can change:
TARGET_PACKAGE = "com.axelbolt.standoff2"


KV = '''
ScreenManager:
    DashboardScreen:
    SettingsScreen:

<DashboardScreen>:
    name: 'dashboard'
    MDBoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 20

        MDLabel:
            text: "Pidor Loader"
            halign: "center"
            font_style: "H4"
            size_hint_y: None
            height: self.texture_size[1]
            theme_text_color: "Custom"
            text_color: 1, 0.2, 0, 1

        Widget:
            size_hint_y: 1

        MDRaisedButton:
            text: "Inject"
            size_hint_x: None
            width: dp(200)
            pos_hint: {"center_x": 0.5}
            md_bg_color: 1, 0.4, 0, 1
            on_release: app.perform_action()

        MDLabel:
            id: version_label
            text: "Version: Loading..."
            halign: "center"

        MDLabel:
            id: changelog_label
            text: "Changelog: Loading..."
            halign: "center"

        Widget:
            size_hint_y: 1

        MDRaisedButton:
            text: "Settings"
            size_hint_x: None
            width: dp(200)
            pos_hint: {"center_x": 0.5}
            md_bg_color: 1, 0.3, 0, 1
            on_release: app.change_screen('settings')

<SettingsScreen>:
    name: 'settings'
    MDBoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 20

        MDLabel:
            text: "Settings"
            font_style: "H5"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 0.4, 0, 1

        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(48)
            spacing: 10
            pos_hint: {"center_x": 0.5}

            MDLabel:
                text: "Method:"
                size_hint_x: None
                width: dp(70)
                valign: "middle"

            MDRaisedButton:
                id: method_button
                text: "Select"
                size_hint_x: None
                width: dp(130)
                md_bg_color: 1, 0.5, 0, 1
                on_release: app.menu.open()

        MDRaisedButton:
            text: "Toggle Dark Mode"
            pos_hint: {"center_x": 0.5}
            md_bg_color: 1, 0.5, 0, 1
            on_release: app.toggle_dark_mode()

        MDRaisedButton:
            text: "Back to Dashboard"
            pos_hint: {"center_x": 0.5}
            md_bg_color: 1, 0.5, 0, 1
            on_release: app.change_screen('dashboard')
'''

class DashboardScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class UltraInjectorApp(MDApp):
    def build(self):
        # Use a built-in close-enough palette
        self.theme_cls.primary_palette = "DeepOrange"
        self.theme_cls.theme_style = "Dark"
        self.root = Builder.load_string(KV)

        # fetch version & changelog
        self.version_url = 'https://pastebin.com/raw/PXP7RnaC'
        self.changelog_url = 'https://pastebin.com/raw/LxqZiP1D'
        UrlRequest(self.version_url, self.update_version, ca_file=certifi.where())
        UrlRequest(self.changelog_url, self.update_changelog, ca_file=certifi.where())

        # Dropdown in settings
        items = [
            {"text": "Patch",  "viewclass": "OneLineListItem", "on_release": lambda x="Patch": self.set_method(x)},
            {"text": "Inject", "viewclass": "OneLineListItem", "on_release": lambda x="Inject": self.set_method(x)},
            {"text": "Die",    "viewclass": "OneLineListItem", "on_release": lambda x="Die": self.set_method(x)},
        ]
        self.menu = MDDropdownMenu(
            caller=self.root.get_screen("settings").ids.method_button,
            items=items,
            width_mult=4,
            max_height=dp(150),
        )
        return self.root

    def set_method(self, m):
        self.root.get_screen("settings").ids.method_button.text = m
        self.menu.dismiss()

    def update_version(self, req, result):
        self.root.get_screen("dashboard").ids.version_label.text = f"Version: {result.strip()}"

    def update_changelog(self, req, result):
        self.root.get_screen("dashboard").ids.changelog_label.text = f"Changelog: {result.strip()}"

    def perform_action(self):
        method = self.root.get_screen("settings").ids.method_button.text
        if method == "Patch":
            message = f"Hooked and patched {TARGET_PACKAGE}"
        elif method == "Inject":
            message = "Injected"
        elif method == "Die":
            message = "Alr goodbye😔"
            Clock.schedule_once(lambda dt: sys.exit(0), 3)
        else:
            message = "No method selected"

        dialog = MDDialog(
            title=method,
            text=message,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()

    def change_screen(self, name):
        self.root.current = name

    def toggle_dark_mode(self):
        t = self.theme_cls
        t.theme_style = "Light" if t.theme_style == "Dark" else "Dark"

if __name__ == '__main__':
    UltraInjectorApp().run()
